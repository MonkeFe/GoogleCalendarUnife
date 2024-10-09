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

    today = date.today()
    
    lista_eventi = ottieniSettimana(today.strftime("%d-%m-%Y"))
    lista_eventi += ottieniSettimana((today + timedelta(days=7)).strftime("%d-%m-%Y"))

    i = 0
    j = 0

    while (i < len(lista_eventi) or j < len(calendarioVecchio)):
      if (i < len(lista_eventi) and j < len(calendarioVecchio)):
        evento_lista_date = datetime.strptime(lista_eventi[i]['start']['dateTime'], "%Y-%m-%dT%H:%M:%S")
        vecchio_evento_date = datetime.strptime(calendarioVecchio[j]['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S")

        if (evento_lista_date == vecchio_evento_date):
          service.events().update(calendarId= calendar_id, eventId = calendarioVecchio[j]["id"], body=lista_eventi[i]).execute()
          i += 1
          j += 1
          print('Event updated')
        elif (evento_lista_date > vecchio_evento_date):
          deleteElement(service, calendarioVecchio[j]["id"], calendar_id)
          j += 1
        else:
          insertElement(service, lista_eventi[i], calendar_id)
          i += 1
      elif (i < len(lista_eventi)):
        insertElement(service, lista_eventi[i], calendar_id)
        i += 1
      elif (j < len(calendarioVecchio)):
        deleteElement(service, calendarioVecchio[j]["id"], calendar_id)
        j += 1
    
  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()