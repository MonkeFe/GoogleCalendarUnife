# Calendario lezioni unife
<div align="center"><img src='https://www.unife.it/it/notizie/news/2019/novembre/sapere-orientare/@@images/4a82e5d7-dd6b-4b2c-93a0-a379a6e89618.jpeg' alt='unife' width="400"></div>
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
6. Salva il file JSON scaricato come credentials.json e sposta il nella directory di lavoro.


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
### Esecuzione
#### Custom
Per eseguire lo script è necessario abilitare l'ambiente virtuale:
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
