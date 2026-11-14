import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_httplib2 import AuthorizedHttp
import httplib2

from modules.logger import logger

SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/gmail.send"]

SERVICES = {
    'calendar': 'v3',
    'gmail': 'v1'
}

def get_user_credentials(): 
    creds = None
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    creds_dir = os.path.join(parent_dir, 'creds')
    user_creds_path = os.path.join(creds_dir, 'credentials.json')
    token_file_path = os.path.join(creds_dir, 'token.json')
    
    try:
        if os.path.exists(token_file_path):
            creds = Credentials.from_authorized_user_file(token_file_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(user_creds_path):
                    logger.error(f"File credenziali non trovato: {user_creds_path}")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(
                    user_creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file_path, 'w') as token:
                token.write(creds.to_json())
    except Exception as e:
        logger.error(f"Errore recupero credenziali Google: {e}")
        return None

    return creds

# returns service {}
def build_service(service_name):
    try:
        creds = get_user_credentials()
        if not creds:
            logger.error(f"Impossibile generare il service '{service_name}': credenziali non valide o mancanti.")
            return None

        service_version = SERVICES.get(service_name)
        if not service_version:
            logger.error(f"Impossibile generare il service '{service_name}': non presente in elenco.")
            return None

        http = httplib2.Http(timeout=600)  # Imposta il timeout a 600 secondi
        authed_http = AuthorizedHttp(creds, http=http)
        service = build(service_name, service_version, http=authed_http)
        return service
    except HttpError as error:
        logger.error(f"Si è verificato un errore HttpError su '{service_name}': {error}")
        return None
    except Exception as error:
        logger.error(f"Errore generico in build_service per '{service_name}': {error}")
        return None
