import requests
import json
from datetime import datetime

materie = {"ISTITUZIONI DI MATEMATICA": "1", "PROGRAMMAZIONE E LABORATORIO" : "2", "ECONOMIA E GESTIONE AZIENDALE" : "3", "LINGUA INGLESE: VERIFICA DELLE CONOSCENZE" : "4"}

#url = "https://aule.unife.it/AgendaStudenti/grid_call.php?view=easycourse&form-type=corso&include=corso&txtcurr=1+-+Percorso+Comune&anno=2024&corso=1233&anno2%5B%5D=PDS0%7C1&date=08-10-2024&periodo_didattico=&_lang=en&list=&week_grid_type=-1&ar_codes_=&ar_select_=&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&all_events=0&faculty_group=0&_lang=en&all_events=0&txtcurr=1+-+Percorso+Comune"
def ottieniSettimana(req_date):
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
    lezioni = response.json()['celle']
    
    if not lezioni:
        return []
    
    for lezione in lezioni:
        if("nome" in lezione):
            continue
        data = datetime.strptime(lezione['data'], "%d-%m-%Y").strftime("%Y-%m-%d")
        oraInizio = datetime.strptime(lezione['ora_inizio'], "%H:%M").strftime("%H:%M")
        oraFine = datetime.strptime(lezione['ora_fine'], "%H:%M").strftime("%H:%M")

        #convert the date and time in the correct format
        start = f"{data}T{oraInizio}:00"
        end = f"{data}T{oraFine}:00"
        
        event = {
            'summary': f"{lezione['nome_insegnamento']} - {lezione['tipo']}",
            'description': lezione['docente'],
            'location': lezione['aula'],
            "colorId": materie[lezione['nome_insegnamento']],
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

def insertElement(service, new_event, calendar_id):
    event = service.events().insert(calendarId=calendar_id, body=new_event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

def deleteElement(service, eventId, calendar_id):
    service.events().delete(calendarId=calendar_id, eventId=eventId).execute()
    print("Event deleted")

def updateElement(service, eventId, body, calendar_id):
    service.events().update(calendarId= calendar_id, eventId = eventId, body=body).execute()
    print("Event update")
