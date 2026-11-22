from typing import Dict, List, Optional, Any
from datetime import date, datetime
from pydantic import BaseModel, Field

# ================= AUTH =================
class AccountBootstrapRequest(BaseModel):
    bootstrap_token: str = Field(..., min_length=20)
    email: str = Field(..., min_length=3, max_length=254)
    company: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=12, max_length=128)

class AccountInviteRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    role: str = Field(..., description="hr, medico o lavoratore")
    employee_identifier: Optional[str] = Field(None, description="Matricola aziendale, usata solo per il calcolo del codice pseudonimo e mai salvata")

class AccountInviteResponse(BaseModel):
    email: str
    role: str
    setup_token: str
    expires_at: str
    delivery_note: str

class AccountSetupRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    setup_token: str = Field(..., min_length=20)
    password: str = Field(..., min_length=12, max_length=128)

class AccountLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=128)

class AccountLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    company: str
    employee_code: Optional[str] = None

class AccountSummary(BaseModel):
    id: int
    email: str
    role: str
    active: bool

# ================= INGESTION =================
class IngestReportResponse(BaseModel):
    timestamp: str
    filename: str
    fogli_trovati: List[str]
    righe_accettate: Dict[str, int]
    righe_scartate: Dict[str, int]
    colonne_ignorate: Dict[str, List[str]]
    errori: List[str]
    messaggio: str

class MappingEntry(BaseModel):
    matricola: str
    codice: str
    reparto: str

# ================= HR =================
class HRKpi(BaseModel):
    punteggio_struttura: float
    fascia_rischio_struttura: str
    reparti_in_rosso_count: int
    reparti_in_rosso: List[str]
    dimissioni_ultimi_12_mesi: int
    costo_turnover_unitario: float
    costo_turnover_stimato: float
    persone_in_carico_medico: int

class HeatmapMatrixEntry(BaseModel):
    reparto: str
    dati_insufficienti: bool
    mesi_valori: Dict[str, Optional[float]]

class HeatmapData(BaseModel):
    mesi: List[str]
    matrix: List[HeatmapMatrixEntry]

class FattoreRischio(BaseModel):
    id: str
    nome: str
    valore: float
    punti: int
    colore: str
    azione_suggerita: Optional[str] = None

class RepartoMetric(BaseModel):
    reparto: str
    mese: str
    organico: int
    dati_insufficienti: bool
    motivo: Optional[str] = None
    punteggio: Optional[float] = None
    fascia: str
    semafori: Dict[str, Any]
    top_3_fattori: List[FattoreRischio]

class HRDashboardResponse(BaseModel):
    mese_riferimento: str
    kpi: HRKpi
    heatmap: HeatmapData
    reparti: List[RepartoMetric]

class AvvisoOrario(BaseModel):
    codice: str
    reparto: str
    mese: str
    tipo_avviso: str  # es: "rientro_sotto_11h" o "turno_12h_o_piu"
    conteggio: int

# ================= MEDICO =================
class OperatoreRischio(BaseModel):
    codice: str
    reparto: str
    ruolo: str
    mese: str
    punteggio: float
    fascia: str
    da_contattare: bool
    stato_presa_in_carico: str
    note_presa_in_carico: Optional[str] = None
    top_3_fattori: List[FattoreRischio]
    semafori: Dict[str, Any]

class PresaInCaricoRequest(BaseModel):
    stato: str = Field(..., description="'contattato', 'in_valutazione', 'concluso'")
    note: Optional[str] = Field(None, description="Note cliniche/organizzative riservate")

class PresaInCaricoResponse(BaseModel):
    codice: str
    stato: str
    note: Optional[str] = None
    data_presa_in_carico: str
    messaggio: str

class TrendMese(BaseModel):
    mese: str
    punteggio: float
    fascia: str

class MedicoSchedaResponse(BaseModel):
    codice: str
    reparto: str
    ruolo: str
    data_assunzione: Optional[str] = None
    ultimo_mese: str
    trend_mensile: List[TrendMese]
    consenso_medico_attivo: bool
    checkin_history: List[Dict[str, Any]]
    presa_in_carico: Dict[str, Any]

# ================= LAVORATORE =================
class CheckinRequest(BaseModel):
    codice: str
    domanda_singola: int = Field(..., ge=1, le=5, description="Punteggio da 1 a 5 (>=3 segnala stress)")
    bat12_risposte: Optional[List[int]] = Field(None, description="12 risposte opzionali (1-5 ciascuna)")
    consenso_medico: bool = Field(False, description="Consenso esplicito alla condivisione con il medico competente")
    richiesta_colloquio: bool = Field(False, description="Richiesta di colloquio confidenziale con il medico")

class CheckinResponse(BaseModel):
    id: int
    codice: str
    data: str
    domanda_singola: int
    bat12_punteggio: Optional[float] = None
    consenso_medico: bool
    richiesta_colloquio: bool
    messaggio_feed: str

class ConsensoUpdateRequest(BaseModel):
    consenso_medico: bool

class LavoratoreStatoResponse(BaseModel):
    codice: str
    reparto: str
    ruolo: str
    punteggio_indicativo: float
    fascia: str
    spiegazione: str
    consenso_medico_attivo: bool
    storico_checkin: List[Dict[str, Any]]
