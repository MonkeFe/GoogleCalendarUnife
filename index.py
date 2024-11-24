from dotenv import load_dotenv
import os
from datetime import datetime

from modules.google_api import build_service
from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, get_semester_from_calendar, get_shared_users_mails
from modules.gmail_api import format_body, send_email

import logging
from logging.handlers import TimedRotatingFileHandler

load_dotenv()

calendar_id = os.getenv("CALENDAR_ID")

def setup_logger(log_file_path):
    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=14)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(handler)
    return logger

def main():
    logger = setup_logger('/home/midee/GoogleCalendarUnife/logs/log.log')
    logger.info('Inizio esecuzione')
    calendar = build_service('calendar', logger)
    mail = build_service('gmail', logger)
    shared_users_mails = get_shared_users_mails(calendar, calendar_id)
    logger.info(shared_users_mails)

    unife_schedule = get_semester_from_unife('1233', 'PDS0|1')
    google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
    modified_events = update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id, logger)
    

    
    if modified_events:
        mail_body = format_body(modified_events)
        #send_email(mail, ['michele.debiagi@edu.unife.it'], 'Modifica Lezioni', mail_body, logger)
        send_email(mail, shared_users_mails, 'Modifica Lezioni', mail_body, logger)
        '''
        '''
    logger.info('Fine esecuzione')


if __name__ == "__main__":
    main()