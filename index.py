from dotenv import load_dotenv

from modules.google_api import build_service
from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, get_semester_from_calendar, get_calendars_info, get_shared_users_mails
from modules.gmail_api import format_body, send_email
from modules.logger import logger

load_dotenv()

# If modifying these scopes, delete the file token.json.

def main():
    calendar = build_service('calendar')
    mail = build_service('gmail')
    
    logger.info('Inizio esecuzione')
    calendars_info = get_calendars_info(calendar)
    for info in calendars_info:
        try:
            logger.info("Processing calendar: " + info['name'])
            calendar_id = info['calendar_id']
            course_id = info['course_id']
            
            shared_users_mails = get_shared_users_mails(calendar, calendar_id)
                
            unife_schedule = get_semester_from_unife(course_id, info["year2"])
            google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
            modified_events = update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id)
        
        except Exception as e:
            logger.error(f"Errore index.py 1: {e}")
            logger.info("Errore calendario")
            continue
        try:
            if modified_events:
                mail_body = format_body(modified_events)
                send_email(mail, shared_users_mails, 'Modifica Lezioni', mail_body)
        except Exception as e:
            logger.error(f"Errore index.py 2 (email): {e}")
            logger.info("Errore email")
            continue



    logger.info('Fine esecuzione')
    logger.info('')
            

if __name__ == "__main__":
    main()