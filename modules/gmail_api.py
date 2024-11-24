from email.mime.text import MIMEText
import base64
from datetime import datetime

def send_email(service, email_adresses, subject, email_message, logger):
    # Creazione del body
    message = MIMEText(email_message, 'html')
    
    # Array di email destinatari
    message['to'] = ', '.join(email_adresses)  # Unisce gli indirizzi email con virgola e spazio
    
    message['subject'] = subject
    
    # Codifica del body
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    # Invio dell'email
    try:
        message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logger.info(f"body inviato. ID: {message['id']}")
    except Exception as e:
        logger.info(f"Si è verificato un errore: {e}")

def switch_key_name(key):
    match key:
        case 'summary':
            return 'Lezione'
        case 'location':
            return 'Aula'
        case 'description':
            return 'Docente'
        case 'end':
            return 'Orario Fine'

def format_body(modified_events):
    created_events = [event for event in modified_events if event['Action'] == 'Created']
    deleted_events = [event for event in modified_events if event['Action'] == 'Deleted']
    updated_events = [event for event in modified_events if event['Action'] == 'Updated']
    
    body = ''
    if created_events:
        body += '<style> table{color:#ffffff}</style>'
        body += '<h1>Lezioni Aggiunte</h1>'

        body += f"<table style='border: 1px solid;border-collapse:collapse;margin-top:3vh;'><th style='border: 1px solid;padding:5px;text-align:center;'>Lezione</th><th style='border: 1px solid;padding:5px;text-align:center;'>Data</th><th style='border: 1px solid;padding:5px;text-align:center;'>Orario</th>"
        
        for event in created_events:
            body += f"<tr style='border: 1px solid;'><td style='border: 1px solid;padding:5px;'>{event['Event']['summary']}</td>"
            body += f"<td style='border: 1px solid;padding:5px;'>{event['Event']['start']['dateTime'][:-9]}</td>"
            body += f"<td style='border: 1px solid;padding:5px;'>{event['Event']['start']['dateTime'][len(event['Event']['start']['dateTime']) - 8 : -3]} - {event['Event']['end']['dateTime'][len(event['Event']['end']['dateTime']) - 8 : -3]}</td></tr>"
        body += "</table>"
        
    
    if deleted_events:
        body += "<h1>Lezioni Cancellate</h1>"
       
        body += f"<table style='border: 1px solid;border-collapse:collapse;margin-top:3vh;'><th style='border: 1px solid;padding:5px;text-align:center;'>Lezione</th><th style='border: 1px solid;padding:5px;text-align:center;'>Data</th><th style='border: 1px solid;padding:5px;text-align:center;'>Orario</th>"
        
        for event in deleted_events:
            body += f"<tr style='border: 1px solid;'><td style='border: 1px solid;padding:5px;'>{event['Event']['summary']}</td>"
            body += f"<td style='border: 1px solid;padding:5px;'>{event['Event']['start']['dateTime'][:- 15]}</td>"
            body += f"<td style='border: 1px solid;padding:5px;'>{event['Event']['start']['dateTime'][len(event['Event']['start']['dateTime']) - 14 : -9]} - {event['Event']['end']['dateTime'][len(event['Event']['end']['dateTime']) - 14 : -9]}</td></tr>"
        body += "</table>"
     
    if updated_events:
        body += "<h1>Lezioni Modificate</h1>"
        currDate = datetime.strptime(updated_events[0]['Event']['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+01:00").date()
        body += f"<h2>{currDate}</h2>"
        for event in updated_events:
            if datetime.strptime(event['Event']['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+01:00").date() != currDate:
                currDate = datetime.strptime(event['Event']['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+01:00").date()
                body += f"<h2>{currDate}</h2>"

            body += f"<h3>{event['Event']['summary']}</h3><i>Per vedere la lezione aggiornata clicca <a href='{event['Event']['htmlLink']}'>qui</a></i><br><p>Modifiche Effettuate:"         
            
            body += f"<table style='border: 1px solid;border-collapse:collapse;margin-top:3vh;'><th style='border: 1px solid;padding:5px;text-align:center;'>Campo Modificato</th><th style='border: 1px solid;padding:5px;text-align:center;'>Valore Precedente</th><th style='border: 1px solid;padding:5px;text-align:center;'>Valore Aggiornato</th>"
            for field in event['ModifiedFields']:
                for key in field:
                    body += f"<tr style='border: 1px solid;'><td style='border: 1px solid;padding:5px;'>{switch_key_name(key)}</td>"
                    body += f"<td style='border: 1px solid;padding:5px;'>{field[key][0]}</td>"
                    body += f"<td style='border: 1px solid;padding:5px;'>{field[key][1]}</td></tr>"
            body += "</table><br>"

    return body