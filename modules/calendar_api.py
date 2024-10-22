import os.path
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import json
import httplib2

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest
from google_auth_httplib2 import AuthorizedHttp

# in caso di modifica degli ambiti, eliminare il file token.json - verrà richiesto nuovo login
SCOPES = ["https://www.googleapis.com/auth/calendar"]

SERVICES = {
    'calendar': 'v3'
}

# Funzione di callback per gestire le risposte delle richieste batch
def callback(request_id, response, exception):
    if exception is not None:
        print(f"Errore nella richiesta {request_id}: {exception}")
        

def get_user_credentials(): 
    creds = None
    # il file token.json memorizza access- e refresh- token dell'utente
    # viene creato in automatico al termine del primo flusso di autorizzazioni
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    creds_dir = os.path.join(parent_dir, 'creds')
    user_creds_path = os.path.join(creds_dir, 'credentials.json')
    token_file_path = os.path.join(creds_dir, 'token.json')
    
    if os.path.exists(token_file_path):
        creds = Credentials.from_authorized_user_file(token_file_path, SCOPES)
    # se file inesistente, o credenziali non valide, richiede il login dell'utente
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # inserire qui: download in locale del file json recuperato da cartella? valutare
            flow = InstalledAppFlow.from_client_secrets_file(
                user_creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # salva token per il prossimo accesso
        with open(token_file_path, 'w') as token:
            token.write(creds.to_json())
        # se scaricato file json credenziali ogni volta, qui eliminare da locale

    return creds

# returns service {}
def build_service(service_name):
    creds = get_user_credentials()
    service_version = SERVICES[service_name]
    
    # Aumenta il timeout di connessione
    http = httplib2.Http(timeout=600)  # Imposta il timeout a 60 secondi
    authed_http = AuthorizedHttp(creds, http=http)
    
    if service_version == None:
        print('impossibile generare il service: non in elenco')
        return None
    try:
        # crea i servizi di interfaccia con Workspace
        service = build(service_name, service_version, http=authed_http)

    except HttpError as error:
        # intercetta errore da API, lo stampa e termina l'esecuzione
        print(f'Si è verificato un errore: {error}')
        return
    
    return service


def insert_element(service, batch, new_event, calendar_id):
    batch.add(service.events().insert(calendarId=calendar_id, body=new_event))
    print('Event created: %', new_event['summary'])

def delete_element(service, batch, event_id, calendar_id):
    batch.add(service.events().delete(calendarId=calendar_id, eventId=event_id))
    print("Event deleted")

def update_element(service, batch, event_id, body, calendar_id):
    batch.add(service.events().update(calendarId= calendar_id, eventId = event_id, body=body))
    print("Event update")

def update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id):
    i = j = 0
    
    batch = BatchHttpRequest(callback=callback, batch_uri='https://www.googleapis.com/batch/calendar/v3')

    while (i < len(unife_schedule) or j < len(google_calendar_events)):
        
        if (len(batch._requests) > 20):
            batch.execute()
            batch = BatchHttpRequest(callback=callback, batch_uri='https://www.googleapis.com/batch/calendar/v3')
            print("Batch updated ", len(batch._requests))
        
        if (i < len(unife_schedule) and j < len(google_calendar_events)):
            date_event_unife = datetime.strptime(unife_schedule[i]['start']['dateTime'], "%Y-%m-%dT%H:%M:%S")
            date_event_google_calendar = datetime.strptime(google_calendar_events[j]['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S")
            
            if (date_event_unife == date_event_google_calendar):
                batch.add(calendar.events().update(calendarId= calendar_id, eventId = google_calendar_events[j]["id"], body=unife_schedule[i]))
                i += 1
                j += 1
                print('Event updated')
            elif (date_event_unife > date_event_google_calendar):
                delete_element(calendar, batch, google_calendar_events[j]["id"], calendar_id)
                j += 1
            else:
                insert_element(calendar, batch, unife_schedule[i], calendar_id)
                i += 1
        elif (i < len(unife_schedule)):
            insert_element(calendar, batch, unife_schedule[i], calendar_id)
            i += 1
        elif (j < len(google_calendar_events)):
            delete_element(calendar, batch, google_calendar_events[j]["id"], calendar_id)
            j += 1
            
    batch.execute()
    print("Batch updated")

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
   
    print('Calendari:')
    for calendar in calendars:
        calendars_name.append(calendar['summary'])
        
        if 'description' in calendar:
            descrption = calendar['description'].split('+')
            if descrption[0] == 'UNIFE-CALENDAR-APP':
                unife_calendars.append({"name": calendar['summary'], "calendar_id": calendar['id'], "course_id": descrption[0], "year2": descrption[1]})
            
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
                
                print(f"Calendario {created_calendar['summary']} creato")
                
                calendars.append(created_calendar['summary'])
                unife_calendars.append({"name": created_calendar['summary'], "calendar_id": created_calendar['id'], "course_id": sub['course_id'], "year2": sub['year2']})
        
        # questo ha un bug in quanto nel caso in cui i calendari che scarica siano in un ordine diverso da quelli nel file calendar.json associa l'anno di corso a calendari sbagliati
        unife_calendars[i]["year2"] = sub["year2"]
                     
    return unife_calendars