from dotenv import load_dotenv
import os

from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, build_service, get_semester_from_calendar, get_calendars_info

load_dotenv()

# If modifying these scopes, delete the file token.json.

def main():
    calendar = build_service('calendar')
    
    calendars_info = get_calendars_info(calendar)
    
    for info in calendars_info:
        print("Processing calendar: " + info['name'])
        calendar_id = info['calendar_id']
        course_id = info['course_id']
        unife_schedule = get_semester_from_unife(course_id, info["year2"])
        google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
        update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id)
    



if __name__ == "__main__":
    main()