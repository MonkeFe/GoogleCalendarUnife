#!/bin/bash

# Spostati nella directory dello script
# cd /home/midee/Documents/uni/scriptCalendario

# Crea un file per verificare l'inizio dell'esecuzione
touch inizio

# Attiva il virtual environment
source .venv/bin/activate

# Specifica esplicitamente l'interprete Python dal venv
.venv/bin/python3.12 ./index.py >> ./logs/cron_output$(date +"%Y_%m_%d__%H_%M_%S").log 2>&1