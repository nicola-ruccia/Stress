export type UserRole = 'admin' | 'hr' | 'medico' | 'lavoratore';
export type FasciaRischio = 'basso' | 'medio' | 'alto' | 'insufficiente';
export type ColoreSemaforo = 'verde' | 'giallo' | 'rosso';

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

export interface HeatmapMatrixEntry {
  reparto: string;
  dati_insufficienti: boolean;
  mesi_valori: Record<string, number | null>;
}

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

export interface HRDashboardResponse {
  mese_riferimento: string;
  kpi: HRKpi;
  heatmap: {
    mesi: string[];
    matrix: HeatmapMatrixEntry[];
  };
  reparti: RepartoMetric[];
}

export interface AvvisoOrario {
  codice: string;
  reparto: string;
  mese: string;
  tipo_avviso: string;
  conteggio: number;
}

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
  semafori: Record<string, any>;
}

export interface MedicoSchedaResponse {
  codice: string;
  reparto: string;
  ruolo: string;
  data_assunzione?: string;
  ultimo_mese: string;
  trend_mensile: Array<{ mese: string; punteggio: number; fascia: FasciaRischio }>;
  consenso_medico_attivo: boolean;
  checkin_history: Array<{
    data: string;
    domanda_singola?: number;
    bat12_punteggio?: number;
    bat12_dettaglio?: string;
    richiesta_colloquio?: boolean;
    consenso_negato?: boolean;
    messaggio?: string;
  }>;
  presa_in_carico: {
    stato: string;
    note?: string;
    data?: string;
  };
}

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  utente_id: string;
  ruolo: string;
  azione: string;
  target_codice?: string;
  note?: string;
}

export interface CheckinPayload {
  codice: string;
  domanda_singola: number;
  bat12_risposte?: number[];
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

export interface IngestReportResponse {
  timestamp: string;
  filename: string;
  fogli_trovati: string[];
  righe_accettate: Record<string, number>;
  righe_scartate: Record<string, number>;
  colonne_ignorate: Record<string, string[]>;
  errori: string[];
  messaggio: string;
}
