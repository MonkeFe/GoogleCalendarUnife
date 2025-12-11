import argparse
from dotenv import load_dotenv

from modules.google_api import build_service
from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, get_semester_from_calendar, get_calendars_info, get_shared_users_mails
from modules.gmail_api import format_body, send_email
from modules.logger import logger

load_dotenv()

def main(send_mail_flag):
    calendar = build_service('calendar')
    mail = build_service('gmail')
    
    logger.info('Inizio esecuzione')
    try:
        calendars_info = get_calendars_info(calendar)
    except Exception as e:
        logger.error("Errore calendars_info (index.py 1): ", e)
    
    
    for info in calendars_info:
        try:
            logger.info("Processing calendar: " + info['name'])
            calendar_id = info['calendar_id']
            course_id = info['course_id']
            extra = info['extra']
            
            shared_users_mails = get_shared_users_mails(calendar, calendar_id)
                
            unife_schedule = get_semester_from_unife(course_id, info["year2"], extra)

            
            google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
            modified_events = update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id)
            
        
        except Exception as e:
            logger.error(f"Errore index.py 2: {e}")
            logger.info("Errore calendario")
            continue
        
        try:
            if modified_events and send_mail_flag:
                mail_body = format_body(modified_events)
                send_email(mail, shared_users_mails, 'Modifica Lezioni', mail_body)
        except Exception as e:
            logger.error(f"Errore index.py 3 (email): {e}")
            logger.info("Errore email")
            continue
        

    logger.info('Fine esecuzione')
    logger.info('-' * 70)
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sendMail", action="store_true", help="Invia email se ci sono modifiche")
    args = parser.parse_args()
    main(args.sendMail)
