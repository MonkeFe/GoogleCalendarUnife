from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from dateutil import parser
import json

from googleapiclient.http import BatchHttpRequest
from modules.logger import logger

LOCAL_TZ = ZoneInfo('Europe/Rome')
BATCH_URI = 'https://www.googleapis.com/batch/calendar/v3'
BATCH_SIZE = 20

def parse_datetime(datetime_str):
    """
    Parse a datetime string and return a naive datetime expressed in Europe/Rome time.
    Aware datetimes (e.g. '...+01:00' or '...Z' returned by Google) are converted to
    local time before dropping the tzinfo, so they compare correctly with the naive
    local datetimes built from the unife schedule.
    """
    if not datetime_str:
        return None
    try:
        dt = parser.parse(datetime_str)
        if dt.tzinfo is not None:
            dt = dt.astimezone(LOCAL_TZ)
        return dt.replace(tzinfo=None)
    except Exception as e:
        logger.error(f"Error parsing datetime (calendar_api.py 2): {datetime_str}, error: {e}")
        return None

def event_key(event):
    """Stable identity of a lesson: start datetime + summary.
    Two events with the same key are the same lesson (duplicates)."""
    start = parse_datetime(event.get('start', {}).get('dateTime'))
    summary = (event.get('summary') or '').strip()
    return (start, summary)

def sort_events(events):
    """Return a new list of events sorted by start then end time."""
    def sort_key(ev):
        s = parse_datetime(ev.get('start', {}).get('dateTime'))
        e = parse_datetime(ev.get('end', {}).get('dateTime'))
        return (s or datetime.min, e or datetime.min)
    return sorted(events, key=sort_key)

def dedupe_events(events):
    """Remove duplicates preserving order based on event_key."""
    seen = set()
    result = []
    for ev in events:
        k = event_key(ev)
        if k in seen:
            continue
        seen.add(k)
        result.append(ev)
    return result

def check_events_diff(event1, event2):
    modified_fields = []

    for key in event1:
        if key in event2:
            if key != 'start' and key != 'end':
                if event1[key] != event2[key]:
                    logger.info(f'\n{event2.get("htmlLink")}: Difference Found in {key}: {event2[key]} --> {event1[key]}')
                    modified_fields.append({key: [event2[key],event1[key]]})
            else:
                dt1 = parse_datetime(event1[key].get('dateTime'))
                dt2 = parse_datetime(event2[key].get('dateTime'))

                if dt1 != dt2:
                    logger.info(f'\n{event2.get("htmlLink")}: Difference Found in {key}: {event2[key]} --> {event1[key]}')
                    modified_fields.append({key: [event2[key],event1[key]]})

    return modified_fields

class _BatchRunner:
    """Collects requests and executes them in chunks, tracking failures."""
    def __init__(self):
        self.failures = 0
        self._new_batch()

    def _new_batch(self):
        self.batch = BatchHttpRequest(callback=self._callback, batch_uri=BATCH_URI)
        self.count = 0

    def _callback(self, request_id, response, exception):
        if exception is not None:
            self.failures += 1
            logger.error(f"Errore nella richiesta (calendar_api.py 1) {request_id}: {exception}")

    def add(self, request):
        self.batch.add(request)
        self.count += 1
        if self.count >= BATCH_SIZE:
            self.flush()

    def flush(self):
        if self.count:
            self.batch.execute()
            logger.info(f"Batch executed ({self.count} requests)")
        self._new_batch()

def update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id):
    """
    Sync google calendar with the unife schedule, matching events by (start, summary).
    - lessons on unife but not on google  -> created
    - lessons on both                      -> updated if something changed
    - events on google but not on unife    -> deleted
    - duplicated events on google          -> extra copies deleted
    """
    modified_events = []

    unife_schedule = dedupe_events(sort_events(unife_schedule))
    google_calendar_events = sort_events(google_calendar_events)

    # Group google events by key, so duplicates are detected
    google_by_key = {}
    for ev in google_calendar_events:
        google_by_key.setdefault(event_key(ev), []).append(ev)

    runner = _BatchRunner()
    created = updated = deleted = duplicates = 0

    for unife_event in unife_schedule:
        key = event_key(unife_event)
        matches = google_by_key.pop(key, [])

        if not matches:
            runner.add(calendar.events().insert(calendarId=calendar_id, body=unife_event))
            logger.info(f'Event created: {unife_event["summary"]} {unife_event["start"]["dateTime"]}')
            modified_events.append({'Event': unife_event, 'Action': 'Created', 'ModifiedFields': []})
            created += 1
            continue

        keep, extra = matches[0], matches[1:]

        differences = check_events_diff(unife_event, keep)
        if differences:
            runner.add(calendar.events().update(calendarId=calendar_id, eventId=keep["id"], body=unife_event))
            logger.info(f'Event updated: {unife_event["summary"]} {unife_event["start"]["dateTime"]}')
            modified_events.append({'Event': keep, 'Action': 'Updated', 'ModifiedFields': differences})
            updated += 1

        # Duplicates are removed silently (not a real change of the schedule)
        for dup in extra:
            runner.add(calendar.events().delete(calendarId=calendar_id, eventId=dup["id"]))
            logger.info(f'Duplicate deleted: {dup.get("summary")} {dup["start"].get("dateTime")}')
            duplicates += 1

    # Whatever is left on google is no longer on unife
    for events in google_by_key.values():
        for i, ev in enumerate(events):
            runner.add(calendar.events().delete(calendarId=calendar_id, eventId=ev["id"]))
            logger.info(f'Event deleted: {ev.get("summary")} {ev.get("start", {}).get("dateTime")}')
            if i == 0:
                modified_events.append({'Event': ev, 'Action': 'Deleted', 'ModifiedFields': []})
            deleted += 1

    runner.flush()
    logger.info(f"Sync done: created {created}, updated {updated}, deleted {deleted}, duplicates removed {duplicates}, failed requests {runner.failures}")

    return modified_events

def get_semester_from_calendar(calendar, calendar_id):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    time_min = week_start.isoformat() + 'T00:00:00Z'

    params = {
        'calendarId': calendar_id,
        'timeMin': time_min,
        'orderBy': 'startTime',
        'singleEvents': True,
        'maxResults': 2500,  # opzionale
    }

    old_calendar_request = calendar.events().list(**params).execute()
    google_calendar_events = old_calendar_request.get('items', [])

    while old_calendar_request.get('nextPageToken'):
        params['pageToken'] = old_calendar_request['nextPageToken']
        old_calendar_request = calendar.events().list(**params).execute()
        google_calendar_events += old_calendar_request.get('items', [])
        params.pop('pageToken', None)

    return google_calendar_events

def get_calendars_info(service):
    calendars_result = service.calendarList().list().execute()
    calendars = calendars_result.get('items', [])
    
    calendars_name = []
    unife_calendars = []
   
    for calendar in calendars:
        calendars_name.append(calendar['summary'])
        
        if 'description' in calendar:
            descrption = calendar['description'].split('+')
            if descrption[0] == 'UNIFE-CALENDAR-APP':
                unife_calendars.append({"name": calendar['summary'], "calendar_id": calendar['id'], "course_id": descrption[1], "year2": descrption[2]})
            
    subjects = []
            
    with open('calendar.json') as f:
        subjects = json.load(f)
    
    for i in range(len(subjects)):
        sub = subjects[i]
        
        if 'name' in sub:
            if sub['name'] not in calendars_name:
                calendar = {
                    'summary': sub['name'],
                    'description': 'UNIFE-CALENDAR-APP+'+ sub['course_id'] + '+' + sub['year2'],
                    'timeZone': 'Europe/Rome',
                }
                created_calendar = service.calendars().insert(body=calendar).execute()
                
                logger.info(f"Calendario {created_calendar['summary']} creato")
                
                calendars.append(created_calendar['summary'])
                unife_calendars.append({"name": created_calendar['summary'], "calendar_id": created_calendar['id'], "course_id": sub['course_id'], "year2": sub['year2']})
                             
    return unife_calendars


def get_shared_users_mails(service, calendar_id):
    shared_users = service.acl().list(calendarId=calendar_id).execute()
    shared_users_mails = []
    
    for user in shared_users['items']:
        if '@edu.unife.it' in user['scope']['value']:
            shared_users_mails.append(user['scope']['value'])
    
    return shared_users_mails
