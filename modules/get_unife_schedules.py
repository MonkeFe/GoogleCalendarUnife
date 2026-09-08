import requests
from datetime import date, timedelta, datetime
import os
import re
from urllib.parse import urlparse, parse_qs
from modules.logger import logger
import json

subjects = {
    # 1° e 2° anno
    "BASI DI DATI E LABORATORIO": "1",
    "LINGUAGGI DI DESCRIZIONE DELL'HARDWARE": "2",
    "SISTEMI OPERATIVI E LABORATORIO": "3",
    "LINGUAGGI DI PROGRAMMAZIONE E LABORATORIO": "4",
    "ALGORITMI E STRUTTURE DATI": "1",
    "CALCOLO NUMERICO E LABORATORIO": "2",
    "TECNOLOGIE WEB": "3",
    "ANALISI MATEMATICA I.B": "4",
    # 3° anno
    "ARCHITETTURA E SVILUPPO SERVIZI INTERNET": "5",
    "CIRCUITI ELETTRICI: FONDAMENTI E LABORATORIO": "6",
    "ECONOMIA E GESTIONE AZIENDALE": "7",
    "INGEGNERIA DEL SOFTWARE": "8",
    "INTELLIGENZA ARTIFICIALE E BIG DATA": "9",
    "RETI DI TELECOMUNICAZIONI": "10",
    "AMMINISTRAZIONE DI SISTEMI, DI RETI E CYBERSECURITY": "11",
    "FONDAMENTI DI AUTOMATICA": "5"
}

DEFAULT_EXCLUDED_SUBJECTS = [
    "ingegneria del software",
    "economia e gestione aziendale",
    "linguaggi e descrizione dell'hardware"
]

def normalize_course_name(name):
    """
    Normalizza il nome di un insegnamento rimuovendo punteggiatura, accenti comuni
    e congiunzioni/preposizioni (di, e, ed, del, dell, ecc.) per un confronto robusto.
    """
    if not name:
        return ""
    s = name.lower()
    s = re.sub(r"['’\-_/()]", ' ', s)
    tokens = [w for w in s.split() if w not in {'di', 'e', 'ed', 'del', 'della', 'dell', 'd', 'dei', 'da'}]
    return ' '.join(tokens)

def is_course_excluded(course_name, exclude_list=None):
    """
    Verifica se un insegnamento è presente nella lista di esclusione.
    """
    if exclude_list is None:
        exclude_list = DEFAULT_EXCLUDED_SUBJECTS
    if not exclude_list or not course_name:
        return False
    norm_course = normalize_course_name(course_name)
    for excl in exclude_list:
        norm_excl = normalize_course_name(excl)
        if norm_excl and (norm_excl == norm_course or norm_excl in norm_course or norm_course in norm_excl):
            return True
    return False

def parse_unife_url(url):
    """
    Estrae i parametri (corso, anno2, anno, txtcurr, date) da un URL AgendaStudenti Unife.
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    course_id = qs.get('corso', [''])[0]
    year2_list = qs.get('anno2[]', []) or qs.get('anno2', [])
    year2 = year2_list[0] if year2_list else ''
    anno = qs.get('anno', [''])[0]
    txtcurr = qs.get('txtcurr', [''])[0]
    req_date = qs.get('date', [''])[0]

    return {
        'course_id': course_id,
        'year2': year2,
        'anno': anno,
        'txtcurr': txtcurr,
        'date': req_date
    }

def getLessonsByDegree(req_date, id_course, year2, anno=None, txtcurr=None):
    url = "https://aule.unife.it/AgendaStudenti/grid_call.php"

    headers = {
        "User-Agent": "Scrivete delle api migliori per scaricare le lezioni, grazie!",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://aule.unife.it",
        "X-Requested-With": "XMLHttpRequest",
    }

    if not anno:
        anno1_env = os.getenv("ANNOSEMESTRE1")
        if anno1_env:
            anno = str(anno1_env)
        else:
            try:
                d = datetime.strptime(req_date, "%d-%m-%Y")
                anno = str(d.year if d.month >= 8 else d.year - 1)
            except Exception:
                anno = str(datetime.today().year)

    if not txtcurr:
        try:
            parts = str(year2).split('|')
            year_num = parts[-1] if len(parts) > 1 else "1"
            txtcurr = f"{year_num} - Percorso Comune"
        except Exception:
            txtcurr = "1 - Percorso Comune"

    payload = {
        "view": "easycourse",
        "form-type": "corso",
        "include": "corso",
        "txtcurr": txtcurr,
        "anno": str(anno),
        "corso": str(id_course),
        "anno2[]": str(year2),
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

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('celle', [])
    except Exception as e:
        logger.error(f"Errore in getLessonsByDegree (corso={id_course}, anno2={year2}, anno={anno}, data={req_date}): {e}")
        return []


def getLessonsByCourse(extra, req_date, anno=None):
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
    if not extra:
        return events

    if not anno:
        anno1_env = os.getenv("ANNOSEMESTRE1")
        if anno1_env:
            anno = str(anno1_env)
        else:
            try:
                d = datetime.strptime(req_date, "%d-%m-%Y")
                anno = str(d.year if d.month >= 8 else d.year - 1)
            except Exception:
                anno = str(datetime.today().year)

    for info in extra:
        try:
            attivita = info.get('attivita')
            if not attivita:
                continue
            payload = {
                "view": "easycourse",
                "_lang": "en",
                "include": "attivita",
                "anno": str(anno),
                "attivita[]": attivita,
                "date": req_date,
                "all_events": "0",
                "txtcurr": ""
            }

            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            events.extend(data.get('celle', []))
        except Exception as e:
            logger.error(f"Errore in getLessonsByCourse (info={info}, data={req_date}): {e}")

    return events

def get_week(req_date, id_course, year2, extra=None, anno=None, txtcurr=None, filter_past=True, exclude=None):
    events_list = []    

    try:
        lessons = getLessonsByDegree(req_date, id_course, year2, anno=anno, txtcurr=txtcurr)
        if extra:
            lessons.extend(getLessonsByCourse(extra, req_date, anno=anno))
    except Exception as e:
        logger.error(f"Errore nel recupero lezioni per la settimana {req_date}: {e}")
        return []
        
    if not lessons:
        return []
    
    for lesson in lessons:
        # Salta elementi di chiusura/sospensione didattica (privi di nome_insegnamento)
        if "nome" in lesson and not lesson.get("nome_insegnamento"):
            continue

        # Salta lezioni annullate
        if lesson.get("Annullato") in ("1", 1):
            continue

        insegnamento = lesson.get('nome_insegnamento', 'Sconosciuto')

        # Salta corsi esclusi dall'utente
        if is_course_excluded(insegnamento, exclude):
            continue

        try:
            date_lesson = datetime.strptime(lesson['data'], "%d-%m-%Y").strftime("%Y-%m-%d")
            start_time = datetime.strptime(lesson['ora_inizio'], "%H:%M").strftime("%H:%M")
            endTime = datetime.strptime(lesson['ora_fine'], "%H:%M").strftime("%H:%M")

            if filter_past:
                current_week_start = datetime.today().date() - timedelta(days=datetime.today().weekday())
                lesson_date_obj = datetime.strptime(date_lesson, "%Y-%m-%d").date()
                if lesson_date_obj < current_week_start:
                    continue

            start = f"{date_lesson}T{start_time}:00"
            end = f"{date_lesson}T{endTime}:00"
            
            tipo = lesson.get('tipo', '').split()[0] if lesson.get('tipo') else 'Lezione'

            event = {
                'summary': f"{tipo} - {insegnamento}",
                'description': lesson.get('docente', ''),
                'location': lesson.get('aula', ''),
                "colorId": subjects.get(insegnamento, "1"),
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
            logger.error(f"Errore nel parsing della lezione: {e}")
    
    return events_list

def get_semester_from_unife(id_course, year2, extra=None, start_date=None, anno=None, txtcurr=None, filter_past=True, exclude=None):
    if extra is None:
        extra = []

    if start_date:
        if isinstance(start_date, (date, datetime)):
            curr_date = start_date if isinstance(start_date, date) else start_date.date()
        else:
            curr_date = datetime.strptime(str(start_date), "%d-%m-%Y").date()
    else:
        curr_date = date.today()

    unife_schedule = []
    
    anno1_env = os.getenv("ANNOSEMESTRE1")
    anno2_env = os.getenv("ANNOSEMESTRE2")

    try:
        anno1 = int(anno) if anno else (int(anno1_env) if anno1_env else curr_date.year)
    except (ValueError, TypeError):
        anno1 = curr_date.year
        logger.warning(f"ANNOSEMESTRE1/anno non valido, usato fallback: {anno1}")

    try:
        anno2 = int(anno2_env) if anno2_env else anno1 + 1
    except (ValueError, TypeError):
        anno2 = anno1 + 1
        logger.warning(f"ANNOSEMESTRE2 non valido, usato fallback: {anno2}")

    try:
        semester_end_date = date(anno1, 12, 31) if curr_date < date(anno1, 11, 15) else date(anno2, 5, 30)
    except Exception as e:
        logger.error(f"Errore calcolo data fine semestre: {e}")
        semester_end_date = curr_date + timedelta(days=120)

    try:
        while curr_date < semester_end_date:
            unife_schedule.extend(get_week(
                curr_date.strftime("%d-%m-%Y"),
                id_course,
                year2,
                extra,
                anno=anno1,
                txtcurr=txtcurr,
                filter_past=filter_past,
                exclude=exclude
            ))
            curr_date += timedelta(days=7)
    except Exception as e:
        logger.error(f"Errore durante il ciclo get_semester_from_unife: {e}")

    return unife_schedule

def get_lessons_from_url(url, start_date=None, extra=None, filter_past=False, exclude=None):
    """
    Estrae i parametri da un URL di AgendaStudenti Unife e scarica tutte le lezioni del semestre,
    escludendo le materie indicate.
    """
    params = parse_unife_url(url)
    if not params['course_id'] or not params['year2']:
        raise ValueError(f"Parametri 'corso' o 'anno2[]' mancanti nell'URL: {url}")

    req_date = start_date or params.get('date') or date.today().strftime("%d-%m-%Y")
    return get_semester_from_unife(
        id_course=params['course_id'],
        year2=params['year2'],
        extra=extra or [],
        start_date=req_date,
        anno=params['anno'],
        txtcurr=params['txtcurr'],
        filter_past=filter_past,
        exclude=exclude
    )