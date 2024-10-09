# Calendario lezioni unife
Questo è un semplice script che scarica le lezioni di informatica dal sito di unife e le carica in automatico su un calendario google.

# Setup
Per il corretto funzionamento del programma bisogna:
- inserire l'id del calendario nel file `.env` come mostrato nel file `.env.example`
- scaricare il file `client_credentials.json` per l'accesso alle api di google
- rinominare il file `client_credentials.json`in `credentials.json`

Installare i pacchetti con:
```bash
pip install -r requirements.txt
```

E poi eseguire il programma con:
  ```bash
  python index.py
  ```
