from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import os
from dateutil import parser
import json

from googleapiclient.http import BatchHttpRequest
from modules.logger import logger

LOCAL_TZ = ZoneInfo('Europe/Rome')
BATCH_URI = 'https://www.googleapis.com/batch/calendar/v3'
BATCH_SIZE = 20

# Funzione di callback per gestire le risposte delle richieste batch
def callback(request_id, response, exception):
    if exception is not None:
        logger.error(f"Errore nella richiesta (calendar_api.py 1) {request_id}: {exception}")

# Helper function to parse dates consistently
def parse_datetime(datetime_str):
    """
    Parse a datetime string and return a naive datetime expressed in Europe/Rome.
    Aware datetimes (e.g. '...Z' or '+01:00') are converted to Europe/Rome before
    dropping the tzinfo, naive ones are assumed to already be in Europe/Rome.
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

def _event_dt(event, field):
    return parse_datetime((event.get(field) or {}).get('dateTime'))

def time_key(event):
    """Key identifying the time slot of an event (start, end)."""
    return (_event_dt(event, 'start'), _event_dt(event, 'end'))

def event_key(event):
    """Create a stable key for an event to help deduplicate items.
    Uses summary, start, end, and location."""
    return (
        (event.get('summary') or '').strip(),
        _event_dt(event, 'start'),
        _event_dt(event, 'end'),
        (event.get('location') or '').strip(),
    )

def sort_events(events):
    """Return a new list of events sorted by start then end time."""
    def sort_key(ev):
        s, e = time_key(ev)
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

def insert_element(service, batch, new_event, calendar_id):
    batch.add(service.events().insert(calendarId=calendar_id, body=new_event))
    logger.info(f'Event created: {new_event["summary"]}')

def delete_element(service, batch, event_id, calendar_id):
    batch.add(service.events().delete(calendarId=calendar_id, eventId=event_id))
    logger.info("Event deleted")

def update_element(service, batch, event_id, body, calendar_id):
    batch.add(service.events().update(calendarId= calendar_id, eventId = event_id, body=body))
    logger.info("Event update")

def check_events_diff(event1, event2):
    """Compare the unife event (event1) with the google event (event2).
    Missing fields on the google side are treated as empty strings
    (Google omits empty description/location)."""
    modified_fields = []

    for key in event1:
        if key in ('start', 'end'):
            dt1 = _event_dt(event1, key)
            dt2 = _event_dt(event2, key)
            if dt1 != dt2:
                logger.info(f'\n{event2.get("htmlLink")}: Difference Found in {key}: {event2.get(key)} --> {event1[key]}')
                modified_fields.append({key: [event2.get(key), event1[key]]})
        else:
            v1 = event1[key] if event1[key] is not None else ''
            v2 = event2.get(key, '')
            if v1 != v2:
                logger.info(f'\n{event2.get("htmlLink")}: Difference Found in {key}: {v2} --> {v1}')
                modified_fields.append({key: [v2, v1]})

    return modified_fields

def _pop_match(pool, predicate):
    """Remove and return the first google event in pool that satisfies predicate."""
    for idx, g in enumerate(pool):
        if predicate(g):
            return pool.pop(idx)
    return None

def update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id):
    """
    Synchronise google calendar with the unife schedule.

    Matching is done by key instead of walking both lists in parallel, so that
    simultaneous lessons and already-duplicated google events are handled correctly:
      1. exact match (summary, start, end, location) -> update only if other fields differ
      2. same time slot and same summary             -> update
      3. same start time                              -> update
      4. unmatched unife events                       -> insert
      5. unmatched google events (incl. duplicates)   -> delete
    """
    modified_events = []

    orig_unife_len = len(unife_schedule)
    unife_schedule = dedupe_events(sort_events(unife_schedule))
    google_pool = sort_events(google_calendar_events)
    logger.info(f"Sync prep: unife {orig_unife_len}->{len(unife_schedule)}, google {len(google_pool)}")

    to_update = []
    to_insert = []

    unmatched = []
    # Pass 1: exact matches, so that they can't be "stolen" by a looser match
    for ev in unife_schedule:
        k = event_key(ev)
        g = _pop_match(google_pool, lambda g: event_key(g) == k)
        if g is not None:
            to_update.append((ev, g))
        else:
            unmatched.append(ev)

    # Pass 2: same time slot and same summary (e.g. classroom changed)
    still_unmatched = []
    for ev in unmatched:
        tk = time_key(ev)
        summary = (ev.get('summary') or '').strip()
        g = _pop_match(google_pool,
                       lambda g: time_key(g) == tk and (g.get('summary') or '').strip() == summary)
        if g is not None:
            to_update.append((ev, g))
        else:
            still_unmatched.append(ev)

    # Pass 3: same start time (e.g. lesson replaced / end time changed)
    for ev in still_unmatched:
        start = _event_dt(ev, 'start')
        g = _pop_match(google_pool, lambda g: start is not None and _event_dt(g, 'start') == start)
        if g is not None:
            to_update.append((ev, g))
        else:
            to_insert.append(ev)

    requests = []
    for ev, g in to_update:
        differences = check_events_diff(ev, g)
        if differences:
            requests.append(calendar.events().update(calendarId=calendar_id, eventId=g["id"], body=ev))
            modified_events.append({'Event': g, 'Action': 'Updated', 'ModifiedFields': differences})
            logger.info(f"Event update: {ev.get('summary')}")

    for ev in to_insert:
        requests.append(calendar.events().insert(calendarId=calendar_id, body=ev))
        modified_events.append({'Event': ev, 'Action': 'Created', 'ModifiedFields': []})
        logger.info(f"Event created: {ev.get('summary')}")

    # Whatever is left in google is either obsolete or a duplicate
    for g in google_pool:
        requests.append(calendar.events().delete(calendarId=calendar_id, eventId=g["id"]))
        modified_events.append({'Event': g, 'Action': 'Deleted', 'ModifiedFields': []})
        logger.info(f"Event deleted: {g.get('summary')} ({(g.get('start') or {}).get('dateTime')})")

    for chunk_start in range(0, len(requests), BATCH_SIZE):
        batch = BatchHttpRequest(callback=callback, batch_uri=BATCH_URI)
        for req in requests[chunk_start:chunk_start + BATCH_SIZE]:
            batch.add(req)
        try:
            batch.execute()
            logger.info(f"Batch executed ({chunk_start // BATCH_SIZE + 1})")
        except Exception as e:
            logger.error(f"Errore durante l'esecuzione del batch: {e}")

    return modified_events

def get_semester_from_calendar(calendar, calendar_id):
    """Return the google events from the start of the current week.
    Returns None (not an empty list) on error, so that the caller does not
    mistake a failed read for an empty calendar and re-insert every lesson."""
    if not calendar:
        logger.error("get_semester_from_calendar chiamato con service calendar None")
        return None
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        time_min = datetime.combine(week_start, datetime.min.time(), tzinfo=LOCAL_TZ).isoformat()

        params = {
            'calendarId': calendar_id,
            'timeMin': time_min,
            'orderBy': 'startTime',
            'singleEvents': True,
            'maxResults': 2500,
        }

        old_calendar_request = calendar.events().list(**params).execute()
        google_calendar_events = old_calendar_request.get('items', [])

        while old_calendar_request.get('nextPageToken'):
            params['pageToken'] = old_calendar_request['nextPageToken']
            old_calendar_request = calendar.events().list(**params).execute()
            google_calendar_events += old_calendar_request.get('items', [])
            params.pop('pageToken', None)

        return google_calendar_events
    except Exception as e:
        logger.error(f"Errore in get_semester_from_calendar per {calendar_id}: {e}")
        return None

def get_calendars_info(service):
    if not service:
        logger.error("get_calendars_info chiamato con service None")
        return []
    try:
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
    except Exception as e:
        logger.error(f"Errore nel recupero della lista calendari: {e}")
        return []
    
    calendars_name = []
    unife_calendars = []
   
    for calendar in calendars:
        summary = calendar.get('summary', '')
        calendars_name.append(summary)
        
        if 'description' in calendar:
            try:
                description = calendar['description'].split('+')
                if description[0] == 'UNIFE-CALENDAR-APP':
                    unife_calendars.append({
                        "name": summary, 
                        "calendar_id": calendar['id'], 
                        "course_id": description[1], 
                        "year2": description[2], 
                        "extra": json.loads(description[3])
                    })
            except Exception as e:
                logger.error(f"Errore nel parsing della descrizione del calendario '{summary}': {e}")
            
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(project_root, 'calendar.json')
    subjects = []
            
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            subjects = json.load(f)
    except Exception as e:
        logger.error(f"Errore nella lettura di {json_path}: {e}")
        subjects = []

    from modules.get_unife_schedules import parse_unife_url
    for sub in subjects:
        if 'url' in sub:
            try:
                parsed_params = parse_unife_url(sub['url'])
                if not sub.get('course_id') and parsed_params.get('course_id'):
                    sub['course_id'] = parsed_params['course_id']
                if not sub.get('year2') and parsed_params.get('year2'):
                    sub['year2'] = parsed_params['year2']
            except Exception as e:
                logger.warning(f"Errore nel parsing dell'URL per {sub.get('name')}: {e}")
        if 'extra' not in sub:
            sub['extra'] = []
    
    subjects_by_name = {sub['name']: sub for sub in subjects if 'name' in sub}

    # Sincronizza i calendari già esistenti con i nuovi parametri di calendar.json se modificati
    for cal_info in unife_calendars:
        name = cal_info['name']
        if name in subjects_by_name:
            sub = subjects_by_name[name]
            cal_info['exclude'] = sub.get('exclude', [])
            updated = False
            if sub.get('course_id') and sub['course_id'] != cal_info['course_id']:
                cal_info['course_id'] = sub['course_id']
                updated = True
            if sub.get('year2') and sub['year2'] != cal_info['year2']:
                cal_info['year2'] = sub['year2']
                updated = True
            if sub.get('extra') is not None and sub['extra'] != cal_info['extra']:
                cal_info['extra'] = sub['extra']
                updated = True
            
            if updated:
                try:
                    new_desc = f"UNIFE-CALENDAR-APP+{cal_info['course_id']}+{cal_info['year2']}+{json.dumps(cal_info['extra'])}"
                    service.calendars().patch(calendarId=cal_info['calendar_id'], body={'description': new_desc}).execute()
                    logger.info(f"Descrizione del calendario '{name}' sincronizzata con calendar.json ({cal_info['year2']})")
                except Exception as e:
                    logger.error(f"Errore nell'aggiornamento della descrizione del calendario '{name}': {e}")
        else:
            cal_info['exclude'] = []
    
    for i in range(len(subjects)):
        sub = subjects[i]
        
        if 'name' in sub:
            if sub['name'] not in calendars_name:
                try:
                    calendar = {
                        'summary': sub['name'],
                        'description': 'UNIFE-CALENDAR-APP+'+ sub['course_id'] + '+' + sub['year2'] + "+" + json.dumps(sub.get('extra', [])),
                        'timeZone': 'Europe/Rome',
                    }
                    created_calendar = service.calendars().insert(body=calendar).execute()
                    
                    logger.info(f"Calendario {created_calendar['summary']} creato")
                    
                    calendars_name.append(created_calendar['summary'])
                    unife_calendars.append({
                        "name": created_calendar['summary'],
                        "calendar_id": created_calendar['id'],
                        "course_id": sub['course_id'],
                        "year2": sub['year2'],
                        "extra": sub.get("extra", []),
                        "exclude": sub.get("exclude", [])
                    })
                except Exception as e:
                    logger.error(f"Errore creazione calendario '{sub['name']}': {e}")
                              
    return unife_calendars


def get_shared_users_mails(service, calendar_id):
    if not service:
        logger.error("get_shared_users_mails chiamato con service None")
        return []
    try:
        shared_users = service.acl().list(calendarId=calendar_id).execute()
        shared_users_mails = []
        
        for user in shared_users.get('items', []):
            scope_val = user.get('scope', {}).get('value', '')
            if '@edu.unife.it' in scope_val:
                shared_users_mails.append(scope_val)
        
        return shared_users_mails
    except Exception as e:
        logger.error(f"Errore in get_shared_users_mails per calendar {calendar_id}: {e}")
        return []
