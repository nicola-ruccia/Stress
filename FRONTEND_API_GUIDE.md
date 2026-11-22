# Guida di Integrazione Frontend - Backend API Rischio Burnout

Questa guida è destinata allo sviluppatore frontend per facilitare l'integrazione con il backend FastAPI.

---

## 1. Quickstart & Indirizzi di Riferimento

- **Base URL Backend**: `http://localhost:8000`
- **Prefisso API**: `/api/v1`
- **Swagger UI Interattiva**: [http://localhost:8000/docs](http://localhost:8000/docs) (permette di testare tutte le chiamate direttamente dal browser e visionare gli schemi JSON)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Specifiche OpenAPI JSON**: [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

### CORS (Cross-Origin Resource Sharing)
Il backend accetta chiamate dalle porte frontend standard:
- `http://localhost:3000` (React / Next.js)
- `http://localhost:5173` (Vite)
- `http://localhost:8080` (Vue)

---

## 2. Le 4 Viste del Software e Flussi Utente

### A. Vista Amministratore / Ingestione Dati
Permette di caricare i dati della clinica e visualizzare il report di validazione:
1. **Precarica Demo**: `POST /api/v1/ingest/load-demo`
   - Popola istantaneamente il database con la clinica finta della demo (150 dipendenti, 6 reparti, 24 mesi di dati, Medicina rossa, Nucleo Alzheimer giallo, ecc.). Utile per sviluppare subito l'interfaccia!
2. **Caricamento Excel reale**: `POST /api/v1/ingest/upload-excel` (multipart/form-data)
   - Valida i 7 fogli Excel (`dipendenti`, `turni`, `assenze`, `ore_mese`, `eventi_hr`, `aggressioni`, `occupazione`).
   - Scarta all'origine qualsiasi colonna non permessa (nomi, CF, note cliniche non entrano mai nel DB).
   - Esegue la pseudonimizzazione immediata delle matricole (HMAC-SHA256 troncato a 10 caratteri).
   - Restituisce il report di importazione (righe accettate, scartate con motivazione).
3. **Download Mapping**: `GET /api/v1/ingest/download-mapping`
   - Scarica il file CSV con l'associazione `matricola -> codice`, destinato **esclusivamente** al medico competente.

---

### B. Vista HR (Risorse Umane / Direzione)
*Regola Privacy Ferrea*: L'HR vede solo dati aggregati per reparto e struttura. **Non vede mai** assenze individuali, check-in individuali o test BAT-12.

1. **Dashboard Globale HR**: `GET /api/v1/hr/dashboard?mese=YYYY-MM&costo_turnover=45000`
   - **4 KPI in alto**:
     - `punteggio_struttura`: punteggio medio da 0 a 100.
     - `fascia_rischio_struttura`: `"basso"`, `"medio"` o `"alto"`.
     - `reparti_in_rosso_count` e `reparti_in_rosso`: lista dei reparti critici.
     - `costo_turnover_stimato`: calcolato come `dimissioni_ultimi_12_mesi * costo_turnover_unitario` (parametro modificabile dall'utente nell'UI).
     - `persone_in_carico_medico`: conteggio totale aggregato anonimo delle persone che il medico competente ha preso in carico.
   - **Mappa di calore (Heatmap)**: matrice `reparti × mesi` con il punteggio per ciascuna cella.
     - *Regola K-Anonymity (`K_MIN = 6`)*: se un reparto ha meno di 6 individui, `dati_insufficienti: true` e il punteggio è mascherato a tutela della privacy.
   - **Elenco Reparti**: per ciascun reparto mostra:
     - `organico`
     - `punteggio` e `fascia`
     - `semafori`: semaforo (verde = 0 punti, giallo = 1, rosso = 2) per ciascuno dei 13 indicatori.
     - `top_3_fattori`: i 3 indicatori che contribuiscono maggiormente al rischio, con `azione_suggerita` allegata (es. per rientri rapidi: *"Rivedere la rotazione dei turni e garantire almeno 11 ore di riposo..."*).
2. **Dettaglio Singolo Reparto**: `GET /api/v1/hr/reparto/{reparto_nome}?mese=YYYY-MM`
3. **Avvisi sull'Orario**: `GET /api/v1/hr/avvisi-orario?mese=YYYY-MM`
   - Codici anonimi con riposo sotto le 11 ore o turni di 12 ore o più.
   - **Nota legale**: questi avvisi non contengono MAI l'etichetta "burnout" o riferimenti alla salute.

---

### C. Vista Medico Competente / Psicologo del Lavoro
Accesso clinico-organizzativo per la prevenzione e presa in carico individuale.

1. **Elenco Operatori a Rischio**: `GET /api/v1/medico/operatori?reparto=Medicina&mese=YYYY-MM`
   - Elenco dei codici pseudonimizzati ordinati per priorità di rischio.
   - `da_contattare: true` (si accende automaticamente se la domanda singola del check-in vale 3 o più oppure se il BAT-12 supera la soglia).
   - `stato_presa_in_carico`: `"non_preso_in_carico"`, `"contattato"`, `"in_valutazione"`, `"concluso"`.
   - `top_3_fattori`: i fattori scatenanti dell'operatore.
2. **Scheda Individuale dell'Operatore**: `GET /api/v1/medico/operatore/{codice}`
   - Ogni chiamata scrive un record indelebile nel registro di audit GDPR.
   - `trend_mensile`: andamento del rischio negli ultimi 12 mesi.
   - `consenso_medico_attivo`: boolean.
   - `checkin_history`: se `consenso_medico_attivo == true`, mostra le risposte fornite dal lavoratore. Se revocato, il backend oscura i dettagli.
3. **Registra Presa in Carico**: `POST /api/v1/medico/presa-in-carico/{codice}`
   - Payload JSON: `{ "stato": "contattato", "note": "Effettuato colloquio preliminare..." }`
   - Aggiorna lo stato e alimenta in automatico il conteggio visibile all'HR.
4. **Registro di Controllo (Audit Trail)**: `GET /api/v1/medico/audit-logs`
   - Elenco accessi per trasparenza e conformità normativa.

---

### D. Vista Lavoratore (Dipendente)
Spazio personale, protetto e anonimo per il singolo operatore.

1. **Accesso con Codice**: `POST /api/v1/lavoratore/accesso?codice=abc1234567`
2. **Visualizzazione del Proprio Stato**: `GET /api/v1/lavoratore/mio-stato/{codice}`
   - Restituisce `punteggio_indicativo`, `fascia` ("basso", "medio", "alto") e `spiegazione` in linguaggio naturale chiaro e non clinico.
   - Storico dei propri check-in compilati e stato del consenso.
3. **Invio Check-in Mensile**: `POST /api/v1/lavoratore/checkin`
   - **Step 1**: Domanda singola da 1 a 5 (*"Quanto ti senti sopraffatto o svuotato dal lavoro?"*).
   - **Step 2**: Se il lavoratore risponde 3, 4 o 5, l'interfaccia sblocca e mostra le 12 domande facoltative del **BAT-12** (Burnout Assessment Tool, scala 1-5).
   - **Step 3**: Toggle *"Condividi questo risultato con il medico competente"* (`consenso_medico: true/false`).
   - **Step 4**: Pulsante *"Richiedi colloquio riservato con il medico"* (`richiesta_colloquio: true/false`).
4. **Modifica Consenso**: `PUT /api/v1/lavoratore/consenso/{codice}`
   - Payload: `{ "consenso_medico": false }`
   - La revoca del consenso ha effetto immediato sulla vista del medico.
5. **Richiesta Colloquio**: `POST /api/v1/lavoratore/richiesta-colloquio/{codice}`

---

## 3. Modelli TypeScript Pronti per il Frontend

Puoi copiare direttamente queste definizioni nel file `types.ts` del tuo progetto frontend:

```typescript
// Ruoli utente
export type UserRole = 'hr' | 'medico' | 'lavoratore' | 'admin';
export type FasciaRischio = 'basso' | 'medio' | 'alto' | 'insufficiente';
export type ColoreSemaforo = 'verde' | 'giallo' | 'rosso';

// KPI Dashboard HR
export interface HRKpi {
  punteggio_struttura: number;
  fascia_rischio_struttura: FasciaRischio;
  reparti_in_rosso_count: number;
  reparti_in_rosso: string[];
  dimissioni_ultimi_12_mesi: number;
  costo_turnover_unitario: number;
  costo_turnover_stimato: number;
  persone_in_carico_medico: number;
}

export interface FattoreRischio {
  id: string;
  nome: string;
  valore: number;
  punti: number;
  colore: ColoreSemaforo;
  azione_suggerita?: string;
}

export interface RepartoMetric {
  reparto: string;
  mese: string;
  organico: number;
  dati_insufficienti: boolean;
  motivo?: string;
  punteggio: number | null;
  fascia: FasciaRischio;
  semafori: Record<string, { valore: number; punti: number; colore: ColoreSemaforo }>;
  top_3_fattori: FattoreRischio[];
}

export interface HeatmapData {
  mesi: string[];
  matrix: {
    reparto: string;
    dati_insufficienti: boolean;
    mesi_valori: Record<string, number | null>;
  }[];
}

export interface HRDashboardResponse {
  mese_riferimento: string;
  kpi: HRKpi;
  heatmap: HeatmapData;
  reparti: RepartoMetric[];
}

// Scheda Medico
export interface OperatoreRischio {
  codice: string;
  reparto: string;
  ruolo: string;
  mese: string;
  punteggio: number;
  fascia: FasciaRischio;
  da_contattare: boolean;
  stato_presa_in_carico: 'non_preso_in_carico' | 'contattato' | 'in_valutazione' | 'concluso';
  note_presa_in_carico?: string;
  top_3_fattori: FattoreRischio[];
}

// Check-in Lavoratore
export interface CheckinPayload {
  codice: string;
  domanda_singola: number; // 1..5
  bat12_risposte?: number[]; // 12 numeri da 1 a 5
  consenso_medico: boolean;
  richiesta_colloquio: boolean;
}

export interface LavoratoreStatoResponse {
  codice: string;
  reparto: string;
  ruolo: string;
  punteggio_indicativo: number;
  fascia: FasciaRischio;
  spiegazione: string;
  consenso_medico_attivo: boolean;
  storico_checkin: Array<{
    data: string;
    domanda_singola: number;
    bat12_punteggio?: number;
    consenso_medico: boolean;
    richiesta_colloquio: boolean;
  }>;
}
```

---

## 4. Gestione Errori e Codici HTTP

- `200 OK`: Operazione completata con successo.
- `400 Bad Request`: Parametri mancanti o non validi (es. codice mancante per lavoratore, file non Excel).
- `404 Not Found`: Operatore o reparto non trovato.
- `500 Internal Server Error`: Errore elaborazione server (il payload include `{ "detail": "messaggio di errore" }`).
