from dotenv import load_dotenv
import os

from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, build_service, get_semester_from_calendar

load_dotenv()

# If modifying these scopes, delete the file token.json.
calendar_id = os.getenv("CALENDAR_ID")

def main():
    calendar = build_service('calendar')

    unife_schedule = get_semester_from_unife()
    google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
    update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id)



if __name__ == "__main__":
    main()