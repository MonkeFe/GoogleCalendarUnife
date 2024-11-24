from datetime import datetime, date, timedelta
import json

from googleapiclient.http import BatchHttpRequest

# Funzione di callback per gestire le risposte delle richieste batch
def callback(request_id, response, exception):
    if exception is not None:
        print(f"Errore nella richiesta {request_id}: {exception}")
        
def insert_element(service, batch, new_event, calendar_id):
    batch.add(service.events().insert(calendarId=calendar_id, body=new_event))
    return {'Event' : new_event, 'Action' : 'Created', 'ModifiedFields': []}

def delete_element(service, batch, old_event, calendar_id):
    batch.add(service.events().delete(calendarId=calendar_id, eventId=old_event["id"]))
    return {'Event' : old_event, 'Action' : 'Deleted', 'ModifiedFields': []}

def update_element(service, batch, old_event, updated_event, calendar_id):
    batch.add(service.events().update(calendarId= calendar_id, eventId = old_event["id"], body=updated_event))
    


def check_events_diff(event1, event2, logger):
    modified_fields = []
    for key in event1:
        if key in event2:
            if key != 'start' and key != 'end':
                if event1[key] != event2[key]:
                    logger.info(f"\n{event2['htmlLink']}: Difference Found in {key}: {event2[key]} --> {event1[key]}")
                    modified_fields.append({key: [event2[key],event1[key]]})
            elif key == 'end':
                date_event1 = datetime.strptime(event1['end']['dateTime'], "%Y-%m-%dT%H:%M:%S")
                date_event2 = datetime.strptime(event2['end']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S")
                if date_event1 != date_event2:
                    logger.info(f"\n{event2['htmlLink']}: Difference Found in {key}: {event2[key]} --> {event1[key]}")
                    modified_fields.append({key: [datetime.strftime(date_event2, "%H:%M"),datetime.strftime(date_event1, "%H:%M")]})
                
    
    return modified_fields

def update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id, logger):
    modified_events = []
    i = j = 0
    
    batch = BatchHttpRequest(callback=callback, batch_uri='https://www.googleapis.com/batch/calendar/v3')

    while (i < len(unife_schedule) or j < len(google_calendar_events)):
        if (len(batch._requests) > 20):
            batch.execute()
            batch = BatchHttpRequest(callback=callback, batch_uri='https://www.googleapis.com/batch/calendar/v3')
            logger.info(f"Batch updated {len(batch._requests)}")
        
        if (i < len(unife_schedule) and j < len(google_calendar_events)):
            date_event_unife = datetime.strptime(unife_schedule[i]['start']['dateTime'], "%Y-%m-%dT%H:%M:%S")
            date_event_google_calendar = datetime.strptime(google_calendar_events[j]['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S")
            
            if (date_event_unife == date_event_google_calendar):
                update_element(calendar, batch, google_calendar_events[j], unife_schedule[i], calendar_id)
                differences = check_events_diff(unife_schedule[i], google_calendar_events[j], logger)
                if differences:
                    modified_events.append({'Event' : google_calendar_events[j], 'Action' : 'Updated', 'ModifiedFields': differences})
                logger.info("Event updated")
                
                i += 1
                j += 1
            elif (date_event_unife > date_event_google_calendar):
                modified_events.append(delete_element(calendar, batch, google_calendar_events[j], calendar_id))
                logger.info("Event deleted")
                j += 1
            else:
                modified_events.append(insert_element(calendar, batch, unife_schedule[i], calendar_id))
                logger.info(f"Event created: {unife_schedule[i]['summary']}")
                i += 1
        elif (i < len(unife_schedule)):
            modified_events.append(insert_element(calendar, batch, unife_schedule[i], calendar_id))
            logger.info(f"Event created: {unife_schedule[i]['summary']}")
            i += 1
        elif (j < len(google_calendar_events)):
            modified_events.append(delete_element(calendar, batch, google_calendar_events[j], calendar_id))
            logger.info("Event deleted")
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

def get_shared_users_mails(service, calendar_id):
    shared_users = service.acl().list(calendarId=calendar_id).execute()
    shared_users_mails = []
    
    for user in shared_users['items']:
        if '@edu.unife.it' in user['scope']['value']:
            shared_users_mails.append(user['scope']['value'])
    
    return shared_users_mails
