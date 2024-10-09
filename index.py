import datetime
import os.path
from richiestaSettimana import *
from dotenv import load_dotenv
from datetime import date, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]
calendar_id = os.getenv("CALENDAR_ID")

def main():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Refer to the Python quickstart on how to setup the environment:
    # https://developers.google.com/calendar/quickstart/python
    # Change the scope to 'https://www.googleapis.com/auth/calendar' and delete any
    # stored credentials.
    calendarioVecchio = service.events().list(calendarId= calendar_id).execute()['items']
    with open("listaEventiCreati.json", "w") as f:
      json.dump(calendarioVecchio, f)

    today = date.today()
    
    lista_eventi = ottieniSettimana(today.strftime("%d-%m-%Y"))
    lista_eventi += ottieniSettimana((today + timedelta(days=7)).strftime("%d-%m-%Y"))

    inseriti = []

    for nuovoEvento in lista_eventi:
      exist, idVecchio = confrontaEventi(nuovoEvento, calendarioVecchio)
      if exist:
        updatedEvent = service.events().update(calendarId= calendar_id, eventId = idVecchio, body=nuovoEvento).execute()
        inseriti.append(idVecchio)
        print('Event updated')
      else:
        event = service.events().insert(calendarId= calendar_id, body=nuovoEvento).execute()
        print('Event created: %s' % (event.get('htmlLink')))
    for x in calendarioVecchio:
      if x["id"] not in inseriti:
        service.events().delete(calendarId= calendar_id, eventId= x["id"]).execute()
        print("Event deleted")
    
  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()