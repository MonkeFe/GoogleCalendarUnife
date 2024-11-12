
from email.mime.text import MIMEText
import base64


def send_email(service, email_adresses, subject, email_message):
    # Creazione del messaggio
    message = MIMEText(email_message, 'html')
    
    # Array di email destinatari
    recipients = email_adresses  # Gli indirizzi email devono essere separati da virgole nella variabile d'ambiente
    message['to'] = ', '.join(recipients)  # Unisce gli indirizzi email con virgola e spazio
    
    message['subject'] = subject
    
    # Codifica del messaggio
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    # Invio dell'email
    try:
        message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        print(f'Messaggio inviato. ID: {message["id"]}')
    except Exception as e:
        print(f'Si è verificato un errore: {e}')