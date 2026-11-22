# Backend PoC - Valutazione e Monitoraggio Rischio Burnout in Sanità Privata

Repository backend modulare sviluppato con **Python 3.11+**, **FastAPI**, **Pandas**, **SQLAlchemy** e **SQLite**. Progettato per essere integrato con il frontend condiviso e pubblicato su GitHub.

Il sistema monitora i fattori organizzativi di rischio burnout in strutture sanitarie e socio-sanitarie (ospedali privati, cliniche, RSA) senza effettuare diagnosi cliniche, segnalando reparti e persone a rischio elevato e motivando in modo trasparente i fattori scatenanti.

---

## 🏛️ Principi Architetturali

1. **Privacy by Design & GDPR**:
   - **Pseudonimizzazione all'import**: le matricole vengono convertite immediatamente in un codice univoco tramite `HMAC-SHA256(matricola, PSEUDO_KEY)` troncato a 10 caratteri. La matricola **non viene mai salvata** nel database.
   - **Whitelist rigida dei campi**: nomi, codici fiscali e diagnosi cliniche non vengono mai memorizzati né processati.
   - **K-Anonymity (`K_MIN = 6`)**: i dati aggregati di reparto sono mostrati solo se riguardano almeno 6 persone; i reparti più piccoli sono mascherati.
   - **Separazione dei ruoli (RBAC)**: l'HR vede solo dati aggregati; il Medico vede i codici individuali e i check-in solo se l'operatore ha prestato il consenso; il Lavoratore vede solo i propri dati.
   - **Registro degli accessi (Audit Trail)**: ogni apertura della scheda di una persona scrive data, utente e ruolo nella tabella `audit_logs`.
2. **Spiegabilità Scientifica (No Black-Box)**:
   - 13 indicatori oggettivi basati su letteratura accreditata (INAIL, BAT-12, Aiken 2002, Vedaa, Dall'Ora 2015).
   - Sistema di semafori (verde=0, giallo=1, rosso=2) e calcolo sintetico trasparente:
     $$\text{Punteggio} = \frac{\sum \text{punti}}{2 \times n_{\text{indicatori}}} \times 100$$
   - Top 3 fattori di rischio esplicativi con azioni correttive suggerite.
   - Soglie configurabili esternamente in `config/soglie.yaml`.

---

## 📁 Struttura del Progetto

```text
burnout-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          # Login simulato con selettore di ruolo
│   │       │   ├── ingest.py        # Upload Excel, caricamento demo, download mapping
│   │       │   ├── hr.py            # Dashboard HR, KPI, Heatmap, Reparti, Avvisi Orario
│   │       │   ├── medico.py        # Elenco operatori a rischio, scheda, presa in carico, audit
│   │       │   ├── lavoratore.py    # Accesso codice, stato personale, check-in, consenso
│   │       │   └── config.py        # Esposizione soglie e azioni suggerite
│   │       └── api.py               # Aggregatore router API v1
│   ├── core/
│   │   ├── config.py                # Pydantic Settings e caricamento soglie.yaml
│   │   ├── privacy.py               # Pseudonimizzazione HMAC, K_MIN, whitelist campi, RBAC
│   │   ├── indicators.py            # Registro e calcolo dei 13 indicatori scientifici
│   │   ├── scoring.py               # Semafori, calcolo punteggio 0-100, top 3 fattori
│   │   └── ingest.py                # Parser Excel 7 fogli e validazione integrità
│   ├── db/
│   │   └── session.py               # Configurazione motore SQLite e sessioni SQLAlchemy
│   ├── models/
│   │   └── entities.py              # Modelli database (Dipendente, Turno, Assenza, Checkin, ecc.)
│   ├── schemas/
│   │   └── schemas.py               # Modelli Pydantic di validazione richiesta/risposta
│   ├── services/
│   │   ├── analytics.py             # Servizi di aggregazione per dashboard HR e Medico
│   │   └── dataset_generator.py     # Generatore dataset clinica demo (150 operatori, 6 reparti)
│   └── main.py                      # Entrata FastAPI, CORS, middleware e lifecycle
├── config/
│   └── soglie.yaml                  # Soglie di rischio, fasce e testi azioni suggerite
├── data/
│   └── genera_dataset.py            # Script autonomo esportazione demo.xlsx e modello_import.xlsx
├── tests/
│   ├── test_indicators.py           # Test unitari calcolo 13 indicatori
│   ├── test_privacy.py              # Test pseudonimizzazione, K_MIN e regole privacy
│   ├── test_scoring.py              # Test semafori e punteggio sintetico
│   └── test_api.py                  # Test endpoint FastAPI con TestClient
├── FRONTEND_API_GUIDE.md            # Guida dettagliata per lo sviluppatore frontend
├── Dockerfile                       # Containerizzazione pronta all'uso
├── docker-compose.yml               # Avvio rapido con docker-compose up
├── requirements.txt                 # Dipendenze Python
├── .env.example                     # File di esempio variabili d'ambiente
└── README.md
```

---

## 🚀 Come Avviare il Progetto (Guida Passo-Passo)

Puoi avviare l'applicazione in **3 modalità diverse** a seconda delle tue esigenze:

---

### Metodo 1: Avvio Locale con Python (Consigliato per Windows / Mac / Linux)

Questo metodo avvia **sia il Backend che l'Interfaccia Web Frontend** su un'unica porta (`8000`), senza bisogno di installare Node.js!

#### Su Windows (PowerShell):
```powershell
# 1. Posizionati nella cartella del progetto
cd C:\Users\nexae\.gemini\antigravity\scratch\burnout-backend

# 2. Crea l'ambiente virtuale Python (se non esiste già)
python -m venv venv

# 3. Attiva l'ambiente virtuale
.\venv\Scripts\Activate.ps1
# (Se PowerShell blocca gli script, esegui prima: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)

# 4. Installa le dipendenze
pip install -r requirements.txt

# 5. Avvia il server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Su Linux / macOS (Bash):
```bash
cd burnout-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 🌐 Dove accedere:
- 🖥️ **Interfaccia Web Completa (Frontend)**: apri nel browser 👉 [http://localhost:8000/](http://localhost:8000/)
- 📑 **Documentazione Interattiva Swagger (API)**: apri 👉 [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Metodo 2: Avvio con Docker (Nessuna dipendenza locale richiesta)

Se hai Docker Desktop installato, puoi avviare tutto con un solo comando:

```bash
docker compose up --build
```
L'applicazione completa sarà subito attiva su:
👉 [http://localhost:8000/](http://localhost:8000/)

---

### Metodo 3: Sviluppo Frontend con Vite & Hot-Reload (Porta 3000)

Se vuoi modificare il codice sorgente React/TypeScript in tempo reale:

```bash
# In un terminale separato (con il backend avviato sulla porta 8000):
cd frontend
npm install
npm run dev
```

L'interfaccia Vite per gli sviluppatori sarà attiva su:
👉 [http://localhost:3000](http://localhost:3000) (inoltrerà in automatico le chiamate API alla porta 8000).

---

## ⚡ Guida alla Demo in 60 Secondi (Come provarlo subito)

Una volta aperto [http://localhost:8000/](http://localhost:8000/) nel browser:

1. **Carica i Dati di Prova**:
   - Vai nella scheda **Dati & Import** e clicca sul pulsante **⚡ Carica Clinica Demo**.
   - Verranno generati all'istante 150 operatori su 6 reparti e 24 mesi di storico.
2. **Esplora la Vista HR**:
   - Clicca su **Vista HR**: vedrai i 4 KPI in alto (costo turnover stimato, reparti in allarme), la **Mappa di Calore** (Heatmap) con il reparto *Medicina* in rosso, i **Top 3 Fattori di Rischio** e le **Azioni Correttive Suggerite**.
3. **Esplora la Vista Medico Competente**:
   - Clicca su **Vista Medico**: visualizzerai l'elenco degli operatori ordinato per punteggio di rischio con la bandiera rossa **DA CONTATTARE**.
   - Clicca su **Apri Scheda** per visualizzare il trend mensile, le risposte del check-in (protette da consenso) e salvare una **Presa in Carico** (che aggiornerà in tempo reale il contatore HR!).
   - Clicca su **Registro Accessi** per verificare l'Audit Trail a norma GDPR.
4. **Esplora la Vista Lavoratore**:
   - Clicca su **Vista Lavoratore**: inserisci un codice (es. uno preso dalla vista medico o copia uno dei codici generati).
   - Compila il **Check-in**: se selezioni un valore da 3 a 5, si sbloccherà automaticamente il questionario validato **BAT-12**.
   - Prova il toggle di revoca del consenso medico per verificare come i dati sanitari vengano oscurati istantaneamente sulla vista del medico!

---

## 🧪 Esecuzione dei Test

Per eseguire l'intera suite di test automatizzati con `pytest`:
```bash
pytest -v
```

---

## 📊 Dataset Sintetico della Clinica Demo

Il backend include un generatore deterministico della clinica demo:
- **150 dipendenti**, **6 reparti**, **24 mesi di storico**:
  - **Medicina (30)**: *Rosso*. Carenza di personale negli ultimi 6 mesi, pazienti per infermiere passati da 6 a 9, rientri rapidi e 3 dimissioni recenti. 4 casi gravi con peggioramento individuale.
  - **Nucleo Alzheimer RSA (30)**: *Giallo*. Segnalazioni di aggressioni frequenti.
  - **Chirurgia (28)**: *Giallo-verde*. Frequenti turni da 12 ore, ma stabili.
  - **Cardiologia (24)**: *Verde*.
  - **Riabilitazione (22)**: *Verde*.
  - **Ambulatori (16)**: *Verde* (solo turni diurni, reparto di confronto).

Per caricare istantaneamente il dataset di prova basta chiamare:
`POST /api/v1/ingest/load-demo` oppure premere l'apposito pulsante nell'interfaccia.

---

## 🤝 Integrazione con il Frontend

Tutte le specifiche per il frontendista (rotte, formati JSON, gestione CORS, modelli TypeScript pronti da copiare) sono documentate in detail in:
👉 [FRONTEND_API_GUIDE.md](file:///C:/Users/nexae/.gemini/antigravity/scratch/burnout-backend/FRONTEND_API_GUIDE.md)

---

## ⚖️ Conformità e Licenze

- **Privacy**: Conforme a GDPR artt. 9 (dati sanitari) e 88 (contesto lavorativo) e allo Statuto dei Lavoratori (Legge 300/1970 art. 4).
- **Metriche**: Basato sulla check-list INAIL per la valutazione dello stress lavoro-correlato e sulla validazione italiana del Burnout Assessment Tool (BAT-12).
