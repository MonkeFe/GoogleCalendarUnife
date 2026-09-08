# Calendario lezioni unife

<br>
<div align="center">

![Language](https://img.shields.io/github/languages/top/MonkeFe/GoogleCalendarUnife.svg?style=for-the-badge&labelColor=black&logo=python&logoColor=blue&label=Python)
![linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![rspberry](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)
![github](https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white)
![WAM](https://img.shields.io/badge/WE%20ARE-MONKEYS-40A02B?style=for-the-badge&labelColor=black)

<img src='https://www.unife.it/it/notizie/news/2019/novembre/sapere-orientare/@@images/4a82e5d7-dd6b-4b2c-93a0-a379a6e89618.jpeg' alt='unife' width="400">
</div>
<br>

Questo è un semplice script che scarica le lezioni di informatica dal sito di unife e le carica in automatico su un calendario google.

## Setup API Google
### Configura l'ambiente
Per completare questa guida rapida, configura il tuo ambiente.

Abilita l'API
Prima di utilizzare le API di Google, devi attivarle in un progetto Google Cloud. Puoi attivare una o più API in un singolo progetto Google Cloud.
Nella console Google Cloud, abilita l'API Google Calendar.

### Abilita l'API

Configurare la schermata per il consenso OAuth
Se utilizzi un nuovo progetto Google Cloud per completare questa guida rapida, configura schermata per il consenso OAuth e aggiungiti come utente di test. Se hai già hai completato questo passaggio per il tuo progetto Cloud, passa alla sezione successiva.

Nella console Google Cloud, vai al Menu menu &gt; API e Servizi &gt; Schermata consenso OAuth.
Vai alla schermata per il consenso OAuth

In Tipo di utente, seleziona Interno, quindi fai clic su Crea.
Compila il modulo di registrazione dell'app, quindi fai clic su Salva e continua.
Per il momento, puoi saltare l'aggiunta di ambiti e fare clic su Salva e continua. In futuro, quando creerai un'app da utilizzare al di fuori del tuo Nell'organizzazione Google Workspace, devi modificare il Tipo di utente in Esterno e poi aggiungi gli ambiti di autorizzazione richiesti dalla tua app.

Esamina il riepilogo della registrazione dell'app. Per apportare modifiche, fai clic su Modifica. Se l'app la registrazione sembra a posto, fai clic su Torna alla Dashboard.
Autorizzare le credenziali per un'applicazione desktop
Per autenticare gli utenti finali e accedere ai dati utente nella tua app, devi: Creare uno o più ID client OAuth 2.0. L'ID client viene utilizzato per identificare singola app ai server OAuth di Google. Se la tua app viene eseguita su più piattaforme, devi creare un ID cliente distinto per ogni piattaforma.
Nella console Google Cloud, vai a Menu menu &gt; API e Servizi &gt; Credenziali.
Vai a credenziali

1. Fai clic su **Crea credenziali** &gt; **ID client OAuth**.
2. Fai clic su **Tipo di applicazione** &gt; **App desktop**.
3. Nel campo **Nome**, digita un nome per la credenziale. Questo nome viene visualizzato solo nella console Google Cloud.
4. Fai clic su **Crea**. Viene visualizzata la schermata di creazione del client OAuth, che mostra il nuovo ID client e il nuovo client secret.
5. Fai clic su **OK**. Le credenziali appena create vengono visualizzate nella sezione **ID client OAuth 2.0**.
6. Salva il file JSON scaricato come credentials.json e sposta il nella directory di lavoro nella cartella creds.


## Setup Progetto
Si consiglia la creazione di un [ambiente virtuale Python](https://docs.python.org/3/library/venv.html) per la gestione delle *dependencies*:
```bash
python3 -m venv <venv_path>
```
Normalmente IDE come Visual Studio Code usano il percorso `.venv` per l'ambiente virtuale.
### Installazione
Installare i pacchetti del progetto con:
```bash
pip install -r requirements.txt
```

> Creare un file `.env` con dentro l'id del calendario, l'anno scolastico del primo semestre e l'anno scolastico del secondo semtre, un esempio si può trovare nel file `.env.example`

### Setup calendari
Il programma sincronizzerà i calendari dei corsi impostati nel file `calendar.json`, per il momento i dati sono impostati a mano in attesa di poter accedere a delle api ufficiali.

---

## 📅 Guida: Cambiare i parametri per il nuovo Anno Accademico

Quando inizia un nuovo anno accademico, occorre aggiornare i parametri di configurazione del progetto per consentire al sistema di scaricare correttamente gli orari delle lezioni aggiornati dal portale Unife.

Di seguito sono riportati i passi da seguire file per file:

### 1. Configurazione delle variabili di ambiente (`.env`)
Nel file `.env` (creato a partire da `.env.example`), aggiornare i due anni relativi ai semestri dell'anno accademico:

```env
ANNOSEMESTRE1=2025
ANNOSEMESTRE2=2026
```
- **`ANNOSEMESTRE1`**: L'anno solare in cui si svolge il **1° Semestre** (es. `2025` per l'anno accademico 2025/2026, indicativamente da settembre a dicembre).
- **`ANNOSEMESTRE2`**: L'anno solare in cui si svolge il **2° Semestre** (es. `2026` per l'anno accademico 2025/2026, indicativamente da febbraio a maggio).

---

### 2. Configurazione del file `calendar.json`
Nel file `calendar.json` sono definite le informazioni sul corso di laurea e sull'anno di corso da sincronizzare. È possibile specificare direttamente l'URL di AgendaStudenti oppure indicare i singoli parametri:

```json
[
    {
        "name": "Informatica (Laurea)",
        "url": "https://aule.unife.it/AgendaStudenti/index.php?view=easycourse&form-type=corso&include=corso&txtcurr=3+-+Percorso+Comune&anno=2026&corso=1233&anno2%5B%5D=PDS0%7C3&date=08-09-2026&periodo_didattico=&_lang=en&list=&week_grid_type=-1&ar_codes_=&ar_select_=&col_cells=0&empty_box=0&only_grid=0&highlighted_date=0&all_events=0&faculty_group=0#",
        "year2": "PDS0|3",
        "course_id": "1233",
        "extra" : []
    }
]
```
- **`url`** *(opzionale)*: URL completo da cui estrarre in automatico `course_id`, `year2`, `anno` e `txtcurr`.
- **`year2`**: Rappresenta l'anno di corso e il relativo Percorso di Studi su EasyCourse/AgendaStudenti Unife (es. `"PDS0|3"` per il 3° anno).
- **`course_id`**: L'ID del corso di laurea sul portale Unife (es. `"1233"` per Informatica).
- **`extra`**: Eventuali codici di insegnamenti o attività didattiche singole/opzionali.

---

### 3. Gestione automatica dell'anno accademico (`modules/get_unife_schedules.py`)
Il parametro `anno` nelle chiamate API Unife viene ora ricavato automaticamente da `ANNOSEMESTRE1` in `.env` (o calcolato in automatico in base alla data della lezione). Non è più necessario modificare manualmente il codice sorgente Python ad ogni cambio di anno accademico!

#### *(Opzionale)* Mappatura dei colori delle materie
In [`modules/get_unife_schedules.py`](file:///home/nicola/Downloads/GoogleCalendarUnife/modules/get_unife_schedules.py), il dizionario `subjects` mappa i nomi degli insegnamenti ai rispettivi ID colore di Google Calendar.

---

### 4. Sincronizzazione automatica con Google Calendar
Quando modifichi `calendar.json` (es. passando da `PDS0|2` a `PDS0|3`), lo script rileva la modifica e aggiorna automaticamente la descrizione del calendario corrispondente su Google Calendar, senza richiedere modifiche manuali o la cancellazione del calendario.

### Esecuzione
- **Sincronizzazione normale**:
  ```bash
  python3 index.py
  ```
- **Con notifica email**:
  ```bash
  python3 index.py --sendMail
  ```
- **Download/Verifica diretta da URL**:
  ```bash
  python3 index.py --url "https://aule.unife.it/AgendaStudenti/..."
  ```

#### Ambiente virtuale
Per eseguire lo script assicurarsi di abilitare l'ambiente virtuale:
```bash
source <venv_path>/bin/activate
```
#### Script
La repository mette a disposizione uno script bash per l'automatizzazione dell'esecuzione:
```bash
./execute
```
#### Automatizzata
Per l'automatizzazione si consiglia l'uso di *utilities* come [`cronie`](https://wiki.archlinux.org/title/Cron) che permettono l'esecuzione periodica di comandi shell:
```bash
crontab -e
# Inserire il percorso dello script da eseguire periodicamente preceduto da N asterischi
0 * * * * /abs/path/to/GoogleCalendarUnife/execute.sh
```
Per cambiare il tempo tra una esecuzione e l'altra (1h come indicato precedentemente) si consiglia la [guida ufficiale](https://crontab.cronhub.io/)

### TO DO
- [ ] Gestione dei corsi facoltativi prevedendo la possibilità di scegliere di quali lezioni visualizzare l'orario