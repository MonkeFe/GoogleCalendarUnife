from dotenv import load_dotenv

from modules.google_api import build_service
from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, get_semester_from_calendar, get_calendars_info
from modules.gmail_api import format_body, send_email

load_dotenv()

# If modifying these scopes, delete the file token.json.

def main():
    calendar = build_service('calendar')
    mail = build_service('gmail')
    
    calendars_info = get_calendars_info(calendar)
    
    for info in calendars_info:
        print("Processing calendar: " + info['name'])
        calendar_id = info['calendar_id']
        course_id = info['course_id']
        unife_schedule = get_semester_from_unife(course_id, info["year2"])
        google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
        modified_events = update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id)
        
        if modified_events:
            mail_body = format_body(modified_events)
            send_email(mail, ['michele.debiagi@edu.unife.it'], 'Modifica Lezioni', mail_body)
        '''
        '''

    



if __name__ == "__main__":
    main()