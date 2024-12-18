import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp
import httplib2

from modules.logger import logger

SCOPES = ["https://www.googleapis.com/auth/calendar", "https://mail.google.com/"]

SERVICES = {
    'calendar': 'v3',
    'gmail': 'v1'
}

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
        logger.error('impossibile generare il service: non in elenco')
        return None
    try:
        # crea i servizi di interfaccia con Workspace
        service = build(service_name, service_version, http=authed_http)

    except HttpError as error:
        # intercetta errore da API, lo stampa e termina l'esecuzione
        logger.error(f'Si è verificato un errore: {error}')
        return
    
    return service
