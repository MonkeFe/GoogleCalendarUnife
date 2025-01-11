from email.mime.text import MIMEText
import base64
from datetime import datetime
from modules.logger import logger


def send_email(service, email_adresses, subject, email_message):
    # Creazione del body
    message = MIMEText(email_message, 'html')
    
    # Array di email destinatari
    message['to'] = email_adresses  # Unisce gli indirizzi email con virgola e spazio
    
    message['subject'] = subject
    
    # Codifica del body
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    # Invio dell'email
    try:
        message = service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logger.info(f'body inviato. ID: {message['id']}')
    except Exception as e:
        logger.error(f'Si è verificato un errore: {e}')

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
    
    
    moved_events = []
    name_deleted_events = [event['Event']['summary'] for event in deleted_events]  
    i = 0

    while len(created_events) > i:
        if created_events[i]['Event']['summary'] in name_deleted_events:
            index_deleted_event = name_deleted_events.index(created_events[i]['Event']['summary'])
            moved_events.append([deleted_events[index_deleted_event], created_events[i]])
            created_events.pop(i)
            deleted_events.pop(index_deleted_event)
            name_deleted_events.pop(index_deleted_event)
        else:
            i += 1

    logger.info(f'Moved events: {moved_events}')
    
    body = ''
    if created_events:
        body += '<style> table{color:#ffffff}</style>'
        body += '<h1>Lezioni Aggiunte</h1>'

        body += f'<table style="border: 1px solid;border-collapse:collapse;margin-top:3vh;"><th style="border: 1px solid;padding:5px;text-align:center;">Lezione</th><th style="border: 1px solid;padding:5px;text-align:center;">Data</th><th style="border: 1px solid;padding:5px;text-align:center;">Orario</th>'
        
        for event in created_events:
            body += f'<tr style="border: 1px solid;"><td style="border: 1px solid;padding:5px;">{event['Event']['summary']}</a></td>'
            body += f'<td style="border: 1px solid;padding:5px;">{event['Event']['start']['dateTime'][:-9]}</td>'
            body += f'<td style="border: 1px solid;padding:5px;">{event['Event']['start']['dateTime'][len(event['Event']['start']['dateTime']) - 8 : -3]} - {event['Event']['end']['dateTime'][len(event['Event']['end']['dateTime']) - 8 : -3]}</td></tr>'
        body += '</table>'
        
    
    if deleted_events:
        body += '<h1>Lezioni Cancellate</h1>'
       
        body += f'<table style="border: 1px solid;border-collapse:collapse;margin-top:3vh;"><th style="border: 1px solid;padding:5px;text-align:center;">Lezione</th><th style="border: 1px solid;padding:5px;text-align:center;">Data</th><th style="border: 1px solid;padding:5px;text-align:center;">Orario</th>'
        
        for event in deleted_events:
            body += f'<tr style="border: 1px solid;"><td style="border: 1px solid;padding:5px;">{event["Event"]['summary']}</td>'
            body += f'<td style="border: 1px solid;padding:5px;">{event['Event']['start']['dateTime'][:- 15]}</td>'
            body += f'<td style="border: 1px solid;padding:5px;">{event['Event']['start']['dateTime'][len(event['Event']['start']['dateTime']) - 14 : -9]} - {event['Event']['end']['dateTime'][len(event['Event']['end']['dateTime']) - 14 : -9]}</td></tr>'
        body += '</table>'
     
    if updated_events:
        body += '<h1>Lezioni Modificate</h1>'
        currDate = datetime.strptime(updated_events[0]['Event']['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+01:00").date()
        body += f'<h2>{currDate}</h2>'
        for event in updated_events:
            if datetime.strptime(event['Event']['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+01:00").date() != currDate:
                currDate = datetime.strptime(event['Event']['start']['dateTime'], "%Y-%m-%dT%H:%M:%S+01:00").date()
                body += f'<h2>{currDate}</h2>'

            body += f'<h3>{event['Event']['summary']}</h3><i>Per vedere la lezione aggiornata clicca <a href="{event['Event']['htmlLink']}">qui</a></i><br><p>Modifiche Effettuate:'          
            
            body += f'<table style="border: 1px solid;border-collapse:collapse;margin-top:3vh;"><th style="border: 1px solid;padding:5px;text-align:center;">Campo Modificato</th><th style="border: 1px solid;padding:5px;text-align:center;">Valore Precedente</th><th style="border: 1px solid;padding:5px;text-align:center;">Valore Aggiornato</th>'
            for field in event['ModifiedFields']:
                for key in field:
                    body += f'<tr style="border: 1px solid;"><td style="border: 1px solid;padding:5px;">{switch_key_name(key)}</td>'
                    body += f'<td style="border: 1px solid;padding:5px;">{field[key][0]}</td>'
                    body += f'<td style="border: 1px solid;padding:5px;">{field[key][1]}</td></tr>'
            body += '</table><br>'


    if moved_events:
        body += '<h1>Lezioni Spostate</h1>'
       
        body += f'<table style="border: 1px solid;border-collapse:collapse;margin-top:3vh;"><th style="border: 1px solid;padding:5px;text-align:center;">Lezione</th><th style="border: 1px solid;padding:5px;text-align:center;">Data Precedente</th><th style="border: 1px solid;padding:5px;text-align:center;">Nuova Data</th>'
        
        for event in moved_events:
            body += f'<tr style="border: 1px solid;"><td style="border: 1px solid;padding:5px;">{event[0]["Event"]['summary']}</td>'
            body += f'<td style="border: 1px solid;padding:5px;">{event[0]['Event']['start']['dateTime'][:- 15]} {event[0]['Event']['start']['dateTime'][len(event[0]['Event']['start']['dateTime']) - 14 : -9]} - {event[0]['Event']['end']['dateTime'][len(event[0]['Event']['end']['dateTime']) - 14 : -9]}</td>'
            body += f'<td style="border: 1px solid;padding:5px;">{event[1]['Event']['start']['dateTime'][:-9]} {event[1]['Event']['start']['dateTime'][len(event[1]['Event']['start']['dateTime']) - 8 : -3]} - {event[1]['Event']['end']['dateTime'][len(event[1]['Event']['end']['dateTime']) - 8 : -3]}</td></tr>'
            
        body += '</table>'

    '''
    with open('email.html', 'w') as f:
        f.write(body)
    '''
    return body