import argparse
from dotenv import load_dotenv

from modules.google_api import build_service
from modules.get_unife_schedules import get_semester_from_unife
from modules.calendar_api import update_calendar, get_semester_from_calendar, get_calendars_info, get_shared_users_mails
from modules.gmail_api import format_body, send_email
from modules.logger import logger

load_dotenv()

def main(send_mail_flag):
    logger.info('Inizio esecuzione')
    calendars_info = []

    try:
        calendar = build_service('calendar')
        mail = build_service('gmail')
        
        if not calendar:
            logger.error("Impossibile procedere: servizio Google Calendar non disponibile.")
            return

        calendars_info = get_calendars_info(calendar)
    except Exception as e:
        logger.error(f"Errore nella fase di inizializzazione in index.py: {e}")

    for info in calendars_info:
        modified_events = []
        shared_users_mails = []
        try:
            cal_name = info.get('name', 'Sconosciuto')
            logger.info("Processing calendar: " + cal_name)
            calendar_id = info['calendar_id']
            course_id = info['course_id']
            extra = info['extra']
            year2 = info['year2']
            exclude = info.get('exclude', None)
            
            shared_users_mails = get_shared_users_mails(calendar, calendar_id)
            unife_schedule = get_semester_from_unife(course_id, year2, extra, exclude=exclude)
            google_calendar_events = get_semester_from_calendar(calendar, calendar_id)
            modified_events = update_calendar(calendar, unife_schedule, google_calendar_events, calendar_id)
            
        except Exception as e:
            logger.error(f"Errore nella elaborazione del calendario '{info.get('name')}': {e}")
            continue
        
        try:
            if modified_events and send_mail_flag:
                mail_body = format_body(modified_events)
                if mail_body and shared_users_mails and mail:
                    send_email(mail, shared_users_mails, 'Modifica Lezioni', mail_body)
                elif not shared_users_mails:
                    logger.info(f"Nessuna email condivisa per il calendario '{info.get('name')}', skip invio mail.")
        except Exception as e:
            logger.error(f"Errore durante l'invio email per '{info.get('name')}': {e}")
            continue

    logger.info('Fine esecuzione')
    logger.info('-' * 70)

if __name__ == "__main__":
    try:
        import json
        parser = argparse.ArgumentParser(description="Sincronizza lezioni Unife con Google Calendar o scarica da URL")
        parser.add_argument("--sendMail", action="store_true", help="Invia email se ci sono modifiche")
        parser.add_argument("--url", type=str, help="Scarica le lezioni direttamente dall'URL specificato di AgendaStudenti Unife")
        parser.add_argument("--exportJson", type=str, help="Salva le lezioni scaricate (da --url) nel file JSON specificato")
        args = parser.parse_args()

        if args.url:
            from modules.get_unife_schedules import get_lessons_from_url
            logger.info(f"Download lezioni dall'URL: {args.url}")
            lessons = get_lessons_from_url(args.url)
            print(f"Scaricamento completato: {len(lessons)} lezioni recuperate per il semestre.")
            if lessons:
                print(f"Prima lezione: {lessons[0]['summary']} ({lessons[0]['start']['dateTime']} -> {lessons[0]['end']['dateTime']})")
                print(f"Ultima lezione: {lessons[-1]['summary']} ({lessons[-1]['start']['dateTime']} -> {lessons[-1]['end']['dateTime']})")
            if args.exportJson:
                with open(args.exportJson, "w", encoding="utf-8") as f:
                    json.dump(lessons, f, ensure_ascii=False, indent=2)
                print(f"Lezioni salvate in: {args.exportJson}")
        else:
            main(args.sendMail)
    except Exception as e:
        logger.error(f"Errore non gestito durante l'esecuzione di index.py: {e}")
