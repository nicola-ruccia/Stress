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

## 🚀 Avvio Rapido

### Opzione 1: Con Python locale

1. **Crea e attiva un virtual environment**:
   ```bash
   python -m venv venv
   # Su Windows:
   venv\Scripts\activate
   # Su Linux/macOS:
   source venv/bin/activate
   ```

2. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Avvia il server di sviluppo**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Apri la documentazione Swagger interattiva**:
   Visita nel browser: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Opzione 2: Con Docker

```bash
docker compose up --build
```
Il backend sarà immediatamente disponibile su `http://localhost:8000`.

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
