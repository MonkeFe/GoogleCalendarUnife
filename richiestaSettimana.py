import requests
import json
from datetime import datetime

#url = "https://aule.unife.it/AgendaStudenti/grid_call.php?view=easycourse&form-type=corso&include=corso&txtcurr=1+-+Percorso+Comune&anno=2024&corso=1233&anno2%5B%5D=PDS0%7C1&date=08-10-2024&periodo_didattico=&_lang=en&list=&week_grid_type=-1&ar_codes_=&ar_select_=&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&all_events=0&faculty_group=0&_lang=en&all_events=0&txtcurr=1+-+Percorso+Comune"
def ottieniSettimana():
    url = "https://aule.unife.it/AgendaStudenti/grid_call.php"
    payload = {
        "view": "easycourse",
        "form-type": "corso",
        "include": "corso",
        "txtcurr": "1 - Percorso Comune",
        "anno": "2024",
        "corso": "1233",
        "anno2[]": "PDS0|1",
        "date": "8-10-2024",
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
    with open("response.json", "w") as f:
        json.dump(lezioni[0], f)
    for lezione in lezioni:
        data = datetime.strptime(lezione['data'], "%d-%m-%Y").strftime("%Y-%m-%d")
        oraInizio = datetime.strptime(lezione['ora_inizio'], "%H:%M").strftime("%H:%M")
        oraFine = datetime.strptime(lezione['ora_fine'], "%H:%M").strftime("%H:%M")

        #convert the date and time in the correct format
        start = f"{data}T{oraInizio}:00"
        end = f"{data}T{oraFine}:00"

        print(start)
        print(end)
        
        event = {
            'summary': lezione['nome_insegnamento'],
            'location': lezione['aula'],
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

def confrontaEventi(nuovoEvento, lista_eventi):
    for vecchioEvento in lista_eventi:
        if datetime.strptime(nuovoEvento['start']['dateTime'], "%Y-%m-%dT%H:%M:%S") == datetime.strptime(vecchioEvento['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"):
            return True, vecchioEvento['id']
    return False, ''
