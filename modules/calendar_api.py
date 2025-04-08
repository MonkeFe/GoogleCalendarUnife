from datetime import date, timedelta
from dateutil import parser
import json

from googleapiclient.http import BatchHttpRequest
from modules.logger import logger

# Funzione di callback per gestire le risposte delle richieste batch
def callback(request_id, response, exception):
    if exception is not None:
        logger.error(f"Errore nella richiesta {request_id}: {exception}")

# Helper function to parse dates consistently
def parse_datetime(datetime_str):
    """Parse a datetime string and return a datetime object, handling timezone information"""
    try:
        return parser.parse(datetime_str)
    except Exception as e:
        logger.error(f"Error parsing datetime: {datetime_str}, error: {e}")
        return None
        
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
    modified_fields = []

    for key in event1:
        if key in event2:
            if key != 'start' and key != 'end':
                if event1[key] != event2[key]:
                    logger.info(f'\n{event2["htmlLink"]}: Difference Found in {key}: {event2[key]} --> {event1[key]}')
                    modified_fields.append({key: [event2[key],event1[key]]})
            elif key == 'end' or key == 'start':
                # Use the new parser for both datetime strings
                dt1 = parse_datetime(event1[key]['dateTime'])
                dt2 = parse_datetime(event2[key]['dateTime'])
                
                if dt1 != dt2:
                    logger.info(f'\n{event2["htmlLink"]}: Difference Found in {key}: {event2[key]} --> {event1[key]}')
                    modified_fields.append({key: [event2[key],event1[key]]})
    
    return modified_fields

def update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id):
    modified_events = []
    i = j = 0
    
    batch = BatchHttpRequest(callback=callback, batch_uri='https://www.googleapis.com/batch/calendar/v3')

    while (i < len(unife_schedule) or j < len(google_calendar_events)):
        if (len(batch._requests) > 20):
            batch.execute()
            batch = BatchHttpRequest(callback=callback, batch_uri='https://www.googleapis.com/batch/calendar/v3')
            logger.info(f"Batch updated {len(batch._requests)}")
        
        if (i < len(unife_schedule) and j < len(google_calendar_events)):
            # Use the new parser for both datetime strings
            date_event_unife = parse_datetime(unife_schedule[i]['start']['dateTime'])
            date_event_google_calendar = parse_datetime(google_calendar_events[j]['start']['dateTime'])
            
            # Compare times ignoring timezone differences
            same_time = False
            if date_event_unife and date_event_google_calendar:
                unife_naive = date_event_unife.replace(tzinfo=None)
                google_naive = date_event_google_calendar.replace(tzinfo=None)
                same_time = unife_naive == google_naive
            
            if same_time:
                batch.add(calendar.events().update(calendarId= calendar_id, eventId = google_calendar_events[j]["id"], body=unife_schedule[i]))
                differences = check_events_diff(unife_schedule[i], google_calendar_events[j])
                if differences:
                    modified_events.append({'Event' : google_calendar_events[j], 'Action' : 'Updated', 'ModifiedFields': differences})
                i += 1
                j += 1
            elif (not date_event_unife or not date_event_google_calendar or 
                  date_event_unife.replace(tzinfo=None) > date_event_google_calendar.replace(tzinfo=None)):
                delete_element(calendar, batch, google_calendar_events[j]["id"], calendar_id)
                modified_events.append({'Event' : google_calendar_events[j], 'Action' : 'Deleted', 'ModifiedFields': []})
                j += 1
            else:
                insert_element(calendar, batch, unife_schedule[i], calendar_id)
                modified_events.append({'Event' : unife_schedule[i], 'Action' : 'Created', 'ModifiedFields': []})

                i += 1
        elif (i < len(unife_schedule)):
            insert_element(calendar, batch, unife_schedule[i], calendar_id)
            modified_events.append({'Event' : unife_schedule[i], 'Action' : 'Created', 'ModifiedFields': []})
            i += 1
        elif (j < len(google_calendar_events)):
            delete_element(calendar, batch, google_calendar_events[j]["id"], calendar_id)
            modified_events.append({'Event' : google_calendar_events[j], 'Action' : 'Deleted', 'ModifiedFields': []})
            j += 1
            
    batch.execute()
    logger.info("Batch updated")

    return modified_events

def get_semester_from_calendar(calendar, calendar_id):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    time_min = week_start.isoformat() + 'T00:00:00Z'

    old_calendar_request = calendar.events().list(calendarId=calendar_id, timeMin=time_min, orderBy='startTime', singleEvents=True).execute()

    google_calendar_events = old_calendar_request['items']
    
    while old_calendar_request.get('nextPageToken'):
        old_calendar_request = calendar.events().list(calendarId= calendar_id, pageToken= old_calendar_request['nextPageToken'], timeMin= time_min).execute()
        google_calendar_events += old_calendar_request['items']
        
    
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