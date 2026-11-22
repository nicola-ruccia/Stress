import {
  HRDashboardResponse,
  RepartoMetric,
  AvvisoOrario,
  OperatoreRischio,
  MedicoSchedaResponse,
  AuditLogEntry,
  LavoratoreStatoResponse,
  CheckinPayload,
  IngestReportResponse,
} from '../types';

const API_BASE = '/api/v1';

export const api = {
  // Ingestione / Demo
  loadDemo: async () => {
    const res = await fetch(`${API_BASE}/ingest/load-demo`, { method: 'POST' });
    if (!res.ok) throw new Error('Errore durante il caricamento della demo');
    return res.json();
  },

  uploadExcel: async (file: File): Promise<IngestReportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/ingest/upload-excel`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Errore nel caricamento del file Excel');
    }
    return res.json();
  },

  getDownloadMappingUrl: () => `${API_BASE}/ingest/download-mapping`,

  // Vista HR
  getHRDashboard: async (mese?: string, costoTurnover?: number): Promise<HRDashboardResponse> => {
    const params = new URLSearchParams();
    if (mese) params.append('mese', mese);
    if (costoTurnover) params.append('costo_turnover', costoTurnover.toString());
    const res = await fetch(`${API_BASE}/hr/dashboard?${params.toString()}`);
    if (!res.ok) throw new Error('Errore nel recupero della dashboard HR');
    return res.json();
  },

  getAvvisiOrario: async (mese?: string): Promise<AvvisoOrario[]> => {
    const params = new URLSearchParams();
    if (mese) params.append('mese', mese);
    const res = await fetch(`${API_BASE}/hr/avvisi-orario?${params.toString()}`);
    if (!res.ok) throw new Error('Errore nel recupero degli avvisi orario');
    return res.json();
  },

  // Vista Medico
  getOperatoriMedico: async (reparto?: string, mese?: string): Promise<OperatoreRischio[]> => {
    const params = new URLSearchParams();
    if (reparto) params.append('reparto', reparto);
    if (mese) params.append('mese', mese);
    const res = await fetch(`${API_BASE}/medico/operatori?${params.toString()}`);
    if (!res.ok) throw new Error('Errore nel recupero degli operatori');
    return res.json();
  },

  getSchedaOperatore: async (codice: string): Promise<MedicoSchedaResponse> => {
    const res = await fetch(`${API_BASE}/medico/operatore/${codice}`);
    if (!res.ok) throw new Error('Errore nel recupero della scheda operatore');
    return res.json();
  },

  salvaPresaInCarico: async (codice: string, stato: string, note?: string) => {
    const res = await fetch(`${API_BASE}/medico/presa-in-carico/${codice}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stato, note }),
    });
    if (!res.ok) throw new Error('Errore nel salvataggio della presa in carico');
    return res.json();
  },

  getAuditLogs: async (): Promise<AuditLogEntry[]> => {
    const res = await fetch(`${API_BASE}/medico/audit-logs?limit=50`);
    if (!res.ok) throw new Error('Errore nel recupero degli audit log');
    return res.json();
  },

  // Vista Lavoratore
  accessoCodice: async (codice: string) => {
    const res = await fetch(`${API_BASE}/lavoratore/accesso?codice=${encodeURIComponent(codice)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Codice operatore non valido o inesistente');
    return res.json();
  },

  getMioStato: async (codice: string): Promise<LavoratoreStatoResponse> => {
    const res = await fetch(`${API_BASE}/lavoratore/mio-stato/${codice}`);
    if (!res.ok) throw new Error('Errore nel recupero del tuo stato');
    return res.json();
  },

  inviaCheckin: async (payload: CheckinPayload) => {
    const res = await fetch(`${API_BASE}/lavoratore/checkin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Errore nell\'invio del check-in');
    return res.json();
  },

  updateConsenso: async (codice: string, consenso_medico: boolean) => {
    const res = await fetch(`${API_BASE}/lavoratore/consenso/${codice}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consenso_medico }),
    });
    if (!res.ok) throw new Error('Errore nell\'aggiornamento del consenso');
    return res.json();
  },

  richiediColloquio: async (codice: string) => {
    const res = await fetch(`${API_BASE}/lavoratore/richiesta-colloquio/${codice}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Errore nella richiesta di colloquio');
    return res.json();
  },

  // Configurazione
  getSoglieConfig: async () => {
    const res = await fetch(`${API_BASE}/config/soglie`);
    if (!res.ok) throw new Error('Errore nel recupero delle soglie');
    return res.json();
  },
};
