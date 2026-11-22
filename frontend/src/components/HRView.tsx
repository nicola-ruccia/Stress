import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { HRDashboardResponse, RepartoMetric, AvvisoOrario, FasciaRischio, ColoreSemaforo } from '../types';
import {
  TrendingUp,
  AlertOctagon,
  Coins,
  UserCheck,
  Building2,
  Calendar,
  Clock,
  CheckCircle,
  HelpCircle,
  Lightbulb,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';

export const HRView: React.FC = () => {
  const [dashboard, setDashboard] = useState<HRDashboardResponse | null>(null);
  const [selectedReparto, setSelectedReparto] = useState<RepartoMetric | null>(null);
  const [costoTurnoverInput, setCostoTurnoverInput] = useState<number>(45000);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'reparti' | 'avvisi'>('reparti');
  const [avvisiOrario, setAvvisiOrario] = useState<AvvisoOrario[]>([]);

  const fetchDashboard = async (costo?: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getHRDashboard(undefined, costo || costoTurnoverInput);
      setDashboard(data);
      if (data.reparti.length > 0) {
        // Seleziona il primo reparto con criticità o il primo disponibile
        const critico = data.reparti.find((r) => r.fascia === 'alto') || data.reparti[0];
        setSelectedReparto(critico);
      }
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento dei dati HR');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvvisi = async () => {
    try {
      const data = await api.getAvvisiOrario();
      setAvvisiOrario(data);
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchAvvisi();
  }, []);

  const getFasciaBadge = (fascia: FasciaRischio) => {
    switch (fascia) {
      case 'alto':
        return <span className="bg-rose-100 text-rose-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase">Alto Rischio</span>;
      case 'medio':
        return <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase">Moderato</span>;
      case 'basso':
        return <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase">Sotto Controllo</span>;
      default:
        return <span className="bg-slate-100 text-slate-600 text-xs font-bold px-2.5 py-1 rounded-full uppercase">Dati Insufficienti</span>;
    }
  };

  const getSemaforoDot = (colore: ColoreSemaforo) => {
    switch (colore) {
      case 'rosso':
        return <span className="w-3 h-3 rounded-full bg-rose-500 shadow-sm shadow-rose-200 inline-block" title="Rosso (2 punti)" />;
      case 'giallo':
        return <span className="w-3 h-3 rounded-full bg-amber-400 shadow-sm shadow-amber-200 inline-block" title="Giallo (1 punto)" />;
      default:
        return <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-200 inline-block" title="Verde (0 punti)" />;
    }
  };

  const getHeatmapColor = (punteggio: number | null, insufficiente: boolean) => {
    if (insufficiente || punteggio === null) return 'bg-slate-100 text-slate-400 border-slate-200';
    if (punteggio >= 66) return 'bg-rose-500 text-white font-bold';
    if (punteggio >= 34) return 'bg-amber-400 text-amber-950 font-bold';
    return 'bg-emerald-500 text-white font-bold';
  };

  if (loading && !dashboard) {
    return (
      <div className="py-20 text-center text-slate-500 flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Caricamento cruscotto direzionale HR in corso...</span>
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="max-w-4xl mx-auto my-12 p-6 bg-rose-50 border border-rose-200 rounded-2xl text-center">
        <AlertOctagon className="w-8 h-8 text-rose-600 mx-auto mb-2" />
        <h3 className="text-base font-bold text-rose-900 mb-1">Nessun dato trovato</h3>
        <p className="text-sm text-rose-700 mb-4">{error}</p>
        <p className="text-xs text-slate-500">
          Vai alla scheda <strong>Dati & Import</strong> e clicca su <strong>⚡ Carica Clinica Demo</strong> per popolare il database.
        </p>
      </div>
    );
  }

  const kpi = dashboard?.kpi;

  return (
    <div className="space-y-8 max-w-7xl mx-auto py-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Cruscotto Direzionale HR & Monitoraggio Reparti</h1>
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Privacy attiva: metriche aggregate per reparto (K_MIN = 6). Nessun dato individuale mostrato all'HR.</span>
          </p>
        </div>

        {/* Tab selection */}
        <div className="flex items-center bg-slate-200/80 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('reparti')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'reparti' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Analisi Reparti & Heatmap
          </button>
          <button
            onClick={() => setActiveTab('avvisi')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'avvisi' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Avvisi Orario ({avvisiOrario.length})</span>
          </button>
        </div>
      </div>

      {/* 4 TOP KPI CARDS */}
      {kpi && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* KPI 1: Rischio Struttura */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Rischio Struttura</span>
              <TrendingUp className="w-4 h-4 text-primary-600" />
            </div>
            <div className="flex items-baseline gap-3 my-1">
              <span className="text-3xl font-extrabold text-slate-900">{kpi.punteggio_struttura}</span>
              <span className="text-xs text-slate-400">/ 100</span>
            </div>
            <div className="mt-2">{getFasciaBadge(kpi.fascia_rischio_struttura)}</div>
          </div>

          {/* KPI 2: Reparti in Rosso */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Reparti in Rosso</span>
              <AlertOctagon className="w-4 h-4 text-rose-600" />
            </div>
            <div className="flex items-baseline gap-2 my-1">
              <span className="text-3xl font-extrabold text-rose-600">{kpi.reparti_in_rosso_count}</span>
              <span className="text-xs text-slate-500">su {dashboard?.reparti.length}</span>
            </div>
            <div className="text-xs text-slate-600 mt-2 truncate font-medium">
              {kpi.reparti_in_rosso.length > 0 ? kpi.reparti_in_rosso.join(', ') : 'Nessun reparto in rosso'}
            </div>
          </div>

          {/* KPI 3: Costo Turnover */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Costo Turnover (12m)</span>
              <Coins className="w-4 h-4 text-amber-600" />
            </div>
            <div className="flex items-baseline gap-1 my-1">
              <span className="text-2xl font-extrabold text-slate-900">
                {kpi.costo_turnover_stimato.toLocaleString('it-IT')} €
              </span>
            </div>
            <div className="text-[11px] text-slate-500 flex items-center justify-between mt-2 pt-2 border-t border-slate-100">
              <span>{kpi.dimissioni_ultimi_12_mesi} dimissioni</span>
              <span className="font-semibold">{costoTurnoverInput.toLocaleString('it-IT')} € / dim.</span>
            </div>
          </div>

          {/* KPI 4: Persone Prese in Carico */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>In Carico al Medico</span>
              <UserCheck className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="flex items-baseline gap-1 my-1">
              <span className="text-3xl font-extrabold text-slate-900">{kpi.persone_in_carico_medico}</span>
              <span className="text-xs text-slate-500">operatori</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-2 flex items-center gap-1">
              <span>Segreto professionale garantito</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'reparti' ? (
        <>
          {/* HEATMAP REPARTI X MESI */}
          {dashboard?.heatmap && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-primary-600" />
                    <span>Mappa di Calore del Rischio (Reparti × Mesi)</span>
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Andamento storico del punteggio sintetico (0-100). Valori &ge; 66 indicano criticità grave.
                  </p>
                </div>
                {/* Legenda */}
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500 inline-block" /><span>Basso (&lt;34)</span></div>
                  <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-amber-400 inline-block" /><span>Medio (34-66)</span></div>
                  <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-rose-500 inline-block" /><span>Alto (&gt;66)</span></div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="py-2.5 px-3 font-semibold text-slate-600">Reparto</th>
                      {dashboard.heatmap.mesi.map((m) => (
                        <th key={m} className="py-2.5 px-3 font-semibold text-slate-600 text-center">{m}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {dashboard.heatmap.matrix.map((row) => (
                      <tr
                        key={row.reparto}
                        onClick={() => {
                          const rep = dashboard.reparti.find((r) => r.reparto === row.reparto);
                          if (rep) setSelectedReparto(rep);
                        }}
                        className={`hover:bg-slate-50/80 cursor-pointer transition-colors ${
                          selectedReparto?.reparto === row.reparto ? 'bg-primary-50/40' : ''
                        }`}
                      >
                        <td className="py-3 px-3 font-medium text-slate-800 flex items-center justify-between">
                          <span>{row.reparto}</span>
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                        </td>
                        {dashboard.heatmap.mesi.map((m) => {
                          const val = row.mesi_valori[m];
                          return (
                            <td key={m} className="py-3 px-2 text-center">
                              <span
                                className={`inline-block w-14 py-1.5 rounded-lg text-xs font-semibold border ${getHeatmapColor(
                                  val,
                                  row.dati_insufficienti
                                )}`}
                                title={row.dati_insufficienti ? 'Dati insufficienti (K<6)' : `Punteggio: ${val}`}
                              >
                                {row.dati_insufficienti ? 'K < 6' : val !== null ? val : '-'}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* DETTAGLIO REPARTO SELEZIONATO */}
          {selectedReparto && (
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-primary-600" />
                    <h2 className="text-xl font-bold text-slate-900">{selectedReparto.reparto}</h2>
                    {getFasciaBadge(selectedReparto.fascia)}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Organico: <strong>{selectedReparto.organico}</strong> persone | Punteggio rischio: <strong>{selectedReparto.punteggio} / 100</strong>
                  </p>
                </div>
              </div>

              {/* TOP 3 FATTORI DI RISCHIO E AZIONI SUGGERITE */}
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-500" />
                  <span>I 3 Fattori Che Pesano di Più & Azioni Correttive Suggerite</span>
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {selectedReparto.top_3_fattori.map((fattore, idx) => (
                    <div
                      key={fattore.id}
                      className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-bold text-slate-400">#{idx + 1}</span>
                          <span className="flex items-center gap-1.5 text-xs font-semibold">
                            {getSemaforoDot(fattore.colore)}
                            <span className="capitalize">{fattore.colore}</span>
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-slate-900">{fattore.nome}</h4>
                        <div className="text-xs text-slate-500 mt-1">
                          Valore medio: <strong>{fattore.valore}</strong> ({fattore.punti} punti)
                        </div>
                      </div>

                      <div className="mt-4 pt-3 border-t border-slate-200 text-xs text-slate-700 bg-white p-2.5 rounded-lg border border-slate-100">
                        <strong className="text-primary-700 flex items-center gap-1 mb-1">
                          <Lightbulb className="w-3.5 h-3.5" /> Azione suggerita:
                        </strong>
                        <p className="text-slate-600 leading-relaxed">{fattore.azione_suggerita}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* MATRICE DEI 13 INDICATORI */}
              <div>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                  Quadro Completo dei 13 Indicatori Rilevati
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 text-xs">
                  {Object.entries(selectedReparto.semafori).map(([id, info]: [string, any]) => (
                    <div key={id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-slate-800 capitalize">{id.replace('_', ' ')}</div>
                        <div className="text-slate-500 font-mono text-[11px] mt-0.5">Val: {info.valore}</div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {getSemaforoDot(info.colore)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        /* TAB AVVISI SULL'ORARIO */
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-amber-600" />
                <span>Avvisi sull'Orario di Lavoro (Riposi e Turni Lunghi)</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Segnalazione tecnica oraria (pause &lt; 11 ore o turni &ge; 12 ore). 
                <strong> Nessuna etichetta di salute o "burnout" è associata a questo elenco.</strong>
              </p>
            </div>
          </div>

          {avvisiOrario.length === 0 ? (
            <div className="text-center py-10 text-slate-400 text-sm">
              Nessun avviso orario rilevato per il mese in esame.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 uppercase font-semibold">
                    <th className="py-2.5 px-3">Codice Anonimo</th>
                    <th className="py-2.5 px-3">Reparto</th>
                    <th className="py-2.5 px-3">Mese</th>
                    <th className="py-2.5 px-3">Tipo Irregolarità Oraria</th>
                    <th className="py-2.5 px-3 text-center">Occorrenze</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {avvisiOrario.map((avv, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-3 px-3 font-mono font-semibold text-slate-800">{avv.codice}</td>
                      <td className="py-3 px-3 text-slate-700">{avv.reparto}</td>
                      <td className="py-3 px-3 text-slate-500">{avv.mese}</td>
                      <td className="py-3 px-3 font-medium text-amber-800">
                        {avv.tipo_avviso === 'pausa_inferiore_11_ore'
                          ? 'Pausa inferiore a 11 ore tra turni'
                          : 'Turno di 12 o più ore consecutive'}
                      </td>
                      <td className="py-3 px-3 text-center font-bold text-slate-900">{avv.conteggio}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
