import requests
from datetime import date, timedelta, datetime
import os
from modules.logger import logger
import json

subjects = {
    "BASI DI DATI E LABORATORIO": "1",
    "LINGUAGGI DI DESCRIZIONE DELL'HARDWARE": "2",
    "SISTEMI OPERATIVI E LABORATORIO": "3",
    "LINGUAGGI DI PROGRAMMAZIONE E LABORATORIO": "4",
    "ALGORITMI E STRUTTURE DATI": "1",
    "CALCOLO NUMERICO E LABORATORIO": "2",
    "TECNOLOGIE WEB": "3",
    "ANALISI MATEMATICA I.B": "4"
}

def getLessonsByDegree(req_date, id_course, year2):
    url = "https://aule.unife.it/AgendaStudenti/grid_call.php"

    headers = {
        "User-Agent": "Scrivete delle api migliori per scaricare le lezioni, grazie!",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://aule.unife.it",
        "X-Requested-With": "XMLHttpRequest",
    }

    payload = {
        "view": "easycourse",
        "form-type": "corso",
        "include": "corso",
        "txtcurr": "2 - Percorso Comune",
        "anno": "2025",
        "corso": id_course,
        "anno2[]": year2, ## caricato da google (quindi modifica la descrizione del calendario) altrimenti calendar.json
        "date": req_date,
        "periodo_didattico": "",
        "_lang": "en",
        "list": "",
        "week_grid_type": "-1",
        "ar_codes_": "",
        "ar_select_": "",
        "col_cells": "0",
        "empty_box": "0",
        "only_grid": "0",
        "highlighted_date": "0",
        "all_events": "0",
        "faculty_group": "0"
    }


    response = requests.post(url, headers=headers, data=payload, timeout=30)

    return response.json()['celle']


def getLessonsByCourse(extra, req_date):
    
    url = "https://aule.unife.it/AgendaStudenti/grid_call.php"

    headers = {
        "User-Agent": "Scrivete delle api migliori per scaricare le lezioni, grazie!",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://aule.unife.it",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    events = []

    for info in extra:

        payload = {
            "view": "easycourse",
            "_lang": "en",
            "include": "attivita",
            "anno": "2025",
            "attivita[]": info['attivita'],
            "date": req_date,  # inserire data nel formato DD-MM-YYYY se necessario
            "all_events": "0",
            "txtcurr": ""
        }

        response = requests.post(url, headers=headers, data=payload, timeout=30)
        events.extend(response.json()['celle'])

    '''
    out_path = os.path.join(os.getcwd(), "unife_events.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    '''

    
    
    return events

    


def get_week(req_date, id_course, year2, extra):

    events_list = []    

    lessons = getLessonsByDegree(req_date, id_course, year2)
    lessons.extend(getLessonsByCourse(extra, req_date))
        
    if not lessons:
        return []
    
    for lesson in lessons:
        if("nome" in lesson):
            continue

        try:

            date_lesson = datetime.strptime(lesson['data'], "%d-%m-%Y").strftime("%Y-%m-%d")
            start_time = datetime.strptime(lesson['ora_inizio'], "%H:%M").strftime("%H:%M")
            endTime = datetime.strptime(lesson['ora_fine'], "%H:%M").strftime("%H:%M")

            # Skip lessons before the current week -- May be removed, we keep this for now
            current_week_start = datetime.today().date() - timedelta(days=datetime.today().weekday())
            lesson_date_obj = datetime.strptime(date_lesson, "%Y-%m-%d").date()
            if lesson_date_obj < current_week_start:
                continue


            
            # convert the date and time in the correct format
            start = f"{date_lesson}T{start_time}:00"
            end = f"{date_lesson}T{endTime}:00"
            
            
            event = {
                'summary': f"{lesson['tipo'].split()[0]} - {lesson['nome_insegnamento']}",
                'description': lesson['docente'],
                'location': lesson['aula'],
                "colorId": subjects[lesson['nome_insegnamento']] if lesson['nome_insegnamento'] in subjects else "1",
                'start': {
                    'dateTime': start,
                    'timeZone': 'Europe/Rome',
                },
                'end': {
                    'dateTime': end,
                    'timeZone': 'Europe/Rome',
                }
                
            }
            events_list.append(event)
        
        except Exception as e:
            logger.error("Errore nel parsing della lezione:", e)

       
    
    
    return events_list

def get_semester_from_unife(id_course, year2, extra):
    curr_date = date.today()
    
    unife_schedule = []
    
    semester_end_date = date(int(os.getenv("ANNOSEMESTRE1")), 12, 31) if date.today() < date(int(os.getenv("ANNOSEMESTRE1")), 11, 15) else date(int(os.getenv("ANNOSEMESTRE2")), 5, 30)

    while curr_date < semester_end_date:
        unife_schedule.extend(get_week(curr_date.strftime("%d-%m-%Y"), id_course, year2, extra))
        curr_date += timedelta(days=7)
    
    return unife_schedule