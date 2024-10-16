import requests
import json
from datetime import date, timedelta, datetime
import os.path

subjects = {"ISTITUZIONI DI MATEMATICA": "1", "PROGRAMMAZIONE E LABORATORIO" : "2", "ECONOMIA E GESTIONE AZIENDALE" : "3", "LINGUA INGLESE: VERIFICA DELLE CONOSCENZE" : "4"}

#url = "https://aule.unife.it/AgendaStudenti/grid_call.php?view=easycourse&form-type=corso&include=corso&txtcurr=1+-+Percorso+Comune&anno=2024&corso=1233&anno2%5B%5D=PDS0%7C1&date=08-10-2024&periodo_didattico=&_lang=en&list=&week_grid_type=-1&ar_codes_=&ar_select_=&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&all_events=0&faculty_group=0&_lang=en&all_events=0&txtcurr=1+-+Percorso+Comune"
def get_week(req_date):
    url = "https://aule.unife.it/AgendaStudenti/grid_call.php"
    payload = {
        "view": "easycourse",
        "form-type": "corso",
        "include": "corso",
        "txtcurr": "1 - Percorso Comune",
        "anno": "2024",
        "corso": "1233",
        "anno2[]": "PDS0|1",
        "date": req_date,
        "periodo_didattico": "",
        "_lang": "en",
        "list": "",
        "week_grid_type": "-1",
        "ar_codes_": "",
        "ar_select_": "",
        "col_cells": "scriptCalendario0",
        "empty_box": "0",
        "only_grid": "0",
        "highlighted_date": "0",
        "all_events": "0",
        "faculty_group": "0",
        "_lang": "en",
        "all_events": "0",
        "txtcurr": "1 - Percorso Comune"
    }

    events_list = []

    response = requests.get(url, params=payload)

    #write in a json file the response in a json econded format
    lessons = response.json()['celle']
    
    if not lessons:
        return []
    
    for lesson in lessons:
        if("nome" in lesson):
            continue
        date_lesson = datetime.strptime(lesson['data'], "%d-%m-%Y").strftime("%Y-%m-%d")
        start_time = datetime.strptime(lesson['ora_inizio'], "%H:%M").strftime("%H:%M")
        endTime = datetime.strptime(lesson['ora_fine'], "%H:%M").strftime("%H:%M")

        #convert the date and time in the correct format
        start = f"{date_lesson}T{start_time}:00"
        end = f"{date_lesson}T{endTime}:00"
        
        event = {
            'summary': f"{lesson['nome_insegnamento']} - {lesson['tipo']}",
            'description': lesson['docente'],
            'location': lesson['aula'],
            "colorId": subjects[lesson['nome_insegnamento']],
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
    return events_list

def get_semester_from_unife():

    curr_date = date.today()
    unife_schedule = []
    semester_end_date = date(int(os.getenv("ANNOSEMESTRE1")), 12, 31) if date.today() < date(int(os.getenv("ANNOSEMESTRE1")), 12, 31) else date(int(os.getenv("ANNOSEMESTRE2")), 5, 30)
    while curr_date < semester_end_date:
        print(curr_date)
        unife_schedule += get_week(curr_date.strftime("%d-%m-%Y"))
        curr_date += timedelta(days=7)
    return unife_schedule