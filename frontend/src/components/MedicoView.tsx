import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { OperatoreRischio, MedicoSchedaResponse, AuditLogEntry, FasciaRischio } from '../types';
import { AuditLogModal } from './AuditLogModal';
import {
  Stethoscope,
  AlertTriangle,
  Flag,
  UserCheck,
  Search,
  Filter,
  CheckCircle2,
  X,
  FileText,
  Lock,
  MessageSquare,
  ShieldAlert,
} from 'lucide-react';

export const MedicoView: React.FC = () => {
  const [operatori, setOperatori] = useState<OperatoreRischio[]>([]);
  const [filteredReparto, setFilteredReparto] = useState<string>('');
  const [repartiDisponibili, setRepartiDisponibili] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Scheda Dettaglio Operatore Modal
  const [schedaOperatore, setSchedaOperatore] = useState<MedicoSchedaResponse | null>(null);
  const [loadingScheda, setLoadingScheda] = useState<boolean>(false);
  const [presaInCaricoStato, setPresaInCaricoStato] = useState<string>('contattato');
  const [presaInCaricoNote, setPresaInCaricoNote] = useState<string>('');
  const [feedbackSalvataggio, setFeedbackSalvataggio] = useState<string | null>(null);

  // Audit Logs Modal
  const [showAuditLogs, setShowAuditLogs] = useState<boolean>(false);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);

  const fetchOperatori = async (rep?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getOperatoriMedico(rep || undefined);
      setOperatori(data);

      // Ricava reparti unici
      const reps = Array.from(new Set(data.map((o) => o.reparto)));
      setRepartiDisponibili(reps);
    } catch (err: any) {
      setError(err.message || 'Errore recupero lista operatori per il medico');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOperatori(filteredReparto);
  }, [filteredReparto]);

  const handleOpenScheda = async (codice: string) => {
    try {
      setLoadingScheda(true);
      setFeedbackSalvataggio(null);
      const data = await api.getSchedaOperatore(codice);
      setSchedaOperatore(data);
      setPresaInCaricoStato(data.presa_in_carico.stato !== 'non_preso_in_carico' ? data.presa_in_carico.stato : 'contattato');
      setPresaInCaricoNote(data.presa_in_carico.note || '');
    } catch (err: any) {
      alert('Errore apertura scheda: ' + err.message);
    } finally {
      setLoadingScheda(false);
    }
  };

  const handleSalvaPresaInCarico = async () => {
    if (!schedaOperatore) return;
    try {
      await api.salvaPresaInCarico(schedaOperatore.codice, presaInCaricoStato, presaInCaricoNote);
      setFeedbackSalvataggio('Presa in carico aggiornata con successo! Il conteggio anonimo HR è stato sincronizzato.');
      // Ricarica la lista per aggiornare lo stato nella tabella
      fetchOperatori(filteredReparto);
    } catch (err: any) {
      alert('Errore nel salvataggio: ' + err.message);
    }
  };

  const handleOpenAudit = async () => {
    try {
      const logs = await api.getAuditLogs();
      setAuditLogs(logs);
      setShowAuditLogs(true);
    } catch (err: any) {
      alert('Errore audit log: ' + err.message);
    }
  };

  const getFasciaBadge = (fascia: FasciaRischio) => {
    switch (fascia) {
      case 'alto':
        return <span className="bg-rose-100 text-rose-800 text-xs font-bold px-2.5 py-0.5 rounded-full">Alto Rischio</span>;
      case 'medio':
        return <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-0.5 rounded-full">Medio</span>;
      default:
        return <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-0.5 rounded-full">Basso</span>;
    }
  };

  const getStatoPresaInCaricoBadge = (stato: string) => {
    switch (stato) {
      case 'contattato':
        return <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded-md">Contattato</span>;
      case 'in_valutazione':
        return <span className="bg-indigo-100 text-indigo-800 text-xs font-semibold px-2 py-0.5 rounded-md">In Valutazione</span>;
      case 'concluso':
        return <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2 py-0.5 rounded-md">Concluso</span>;
      default:
        return <span className="bg-slate-100 text-slate-500 text-xs font-semibold px-2 py-0.5 rounded-md">Non preso in carico</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto py-6">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Stethoscope className="w-6 h-6 text-primary-600" />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Triage & Sorveglianza Sanitaria (Medico Competente)
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Individuazione precoce dei singoli operatori a rischio elevato, visualizzazione check-in (con consenso) e presa in carico riservata.
          </p>
        </div>

        <button
          onClick={handleOpenAudit}
          className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-xl text-xs font-semibold transition-colors"
        >
          <ShieldAlert className="w-4 h-4 text-slate-500" />
          <span>Registro Accessi (Audit Trail)</span>
        </button>
      </div>

      {/* Filter and stats bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-600">Filtra Reparto:</span>
          <select
            value={filteredReparto}
            onChange={(e) => setFilteredReparto(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-3 py-1.5 bg-white text-slate-800 font-medium focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Tutti i reparti ({operatori.length} operatori)</option>
            {repartiDisponibili.map((rep) => (
              <option key={rep} value={rep}>{rep}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-rose-700 font-semibold bg-rose-50 px-3 py-1.5 rounded-lg border border-rose-200">
            <Flag className="w-4 h-4 text-rose-600" />
            <span>{operatori.filter((o) => o.da_contattare).length} Da Contattare (Check-in &ge; 3 o BAT-12)</span>
          </div>
        </div>
      </div>

      {/* OPERATORI TABLE */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="text-center py-16 text-slate-500 text-sm">Caricamento elenco operatori...</div>
        ) : operatori.length === 0 ? (
          <div className="text-center py-16 text-slate-400 text-sm">Nessun operatore trovato per i filtri selezionati.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase">
                  <th className="py-3 px-4">Codice Anonimo</th>
                  <th className="py-3 px-4">Reparto</th>
                  <th className="py-3 px-4">Ruolo</th>
                  <th className="py-3 px-4 text-center">Punteggio Rischio</th>
                  <th className="py-3 px-4 text-center">Fascia</th>
                  <th className="py-3 px-4 text-center">Flag Allerta</th>
                  <th className="py-3 px-4">Stato Presa in Carico</th>
                  <th className="py-3 px-4 text-right">Azione</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {operatori.map((op) => (
                  <tr
                    key={op.codice}
                    className={`hover:bg-slate-50/80 transition-colors ${op.da_contattare ? 'bg-rose-50/30' : ''}`}
                  >
                    <td className="py-3 px-4 font-mono font-bold text-slate-800">{op.codice}</td>
                    <td className="py-3 px-4 font-medium text-slate-700">{op.reparto}</td>
                    <td className="py-3 px-4 text-slate-500 capitalize">{op.ruolo}</td>
                    <td className="py-3 px-4 text-center font-extrabold text-slate-900">{op.punteggio}</td>
                    <td className="py-3 px-4 text-center">{getFasciaBadge(op.fascia)}</td>
                    <td className="py-3 px-4 text-center">
                      {op.da_contattare ? (
                        <span className="inline-flex items-center gap-1 bg-rose-600 text-white font-bold px-2.5 py-0.5 rounded-full text-[11px] animate-pulse">
                          <Flag className="w-3 h-3" /> DA CONTATTARE
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">{getStatoPresaInCaricoBadge(op.stato_presa_in_carico)}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenScheda(op.codice)}
                        className="bg-primary-50 text-primary-700 hover:bg-primary-100 font-semibold px-3 py-1.5 rounded-lg border border-primary-200 transition-colors text-xs"
                      >
                        Apri Scheda
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* MODAL SCHEDA INDIVIDUALE */}
      {schedaOperatore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden my-8">
            {/* Header Scheda */}
            <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase bg-primary-100 text-primary-800 font-bold px-2 py-0.5 rounded-md">
                    Dossier Riservato
                  </span>
                  <h2 className="text-xl font-bold text-slate-900 font-mono">Codice: {schedaOperatore.codice}</h2>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Reparto: <strong>{schedaOperatore.reparto}</strong> | Ruolo: <strong>{schedaOperatore.ruolo}</strong> | Mese attivo: <strong>{schedaOperatore.ultimo_mese}</strong>
                </p>
              </div>

              <button
                onClick={() => setSchedaOperatore(null)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200/50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
              {/* TREND STORICO MENSILE */}
              <div>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Andamento Punteggio di Rischio (Ultimi Mesi)
                </h3>
                <div className="flex items-center gap-2 overflow-x-auto py-2">
                  {schedaOperatore.trend_mensile.map((t) => (
                    <div key={t.mese} className="bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-center min-w-[70px]">
                      <div className="text-[10px] text-slate-400">{t.mese}</div>
                      <div className="text-sm font-bold text-slate-900 mt-0.5">{t.punteggio}</div>
                      <div className="mt-1">{getFasciaBadge(t.fascia)}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* SEZIONE CHECK-IN & CONSENSO MEDICO */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-primary-600" />
                    <span>Esito Check-in e Test BAT-12 dell'Operatore</span>
                  </h3>
                  {schedaOperatore.consenso_medico_attivo ? (
                    <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Consenso Attivo
                    </span>
                  ) : (
                    <span className="text-xs bg-amber-100 text-amber-800 font-semibold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <Lock className="w-3.5 h-3.5" /> Consenso Negato/Revocato
                    </span>
                  )}
                </div>

                {!schedaOperatore.consenso_medico_attivo ? (
                  <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-xs text-amber-800">
                    <strong>Tutela Privacy (GDPR art. 9):</strong> L'operatore ha revocato o non ha prestato il consenso alla condivisione delle risposte del check-in con il medico competente. I dettagli delle risposte sono automaticamente oscurati dal sistema.
                  </div>
                ) : schedaOperatore.checkin_history.length === 0 ? (
                  <p className="text-xs text-slate-400">Nessun check-in compilato dall'operatore.</p>
                ) : (
                  <div className="space-y-3">
                    {schedaOperatore.checkin_history.map((chk, i) => (
                      <div key={i} className="bg-white p-3.5 rounded-xl border border-slate-200 text-xs space-y-1.5">
                        <div className="flex justify-between items-center text-slate-500">
                          <span>Data compilazione: <strong>{chk.data}</strong></span>
                          {chk.richiesta_colloquio && (
                            <span className="bg-rose-100 text-rose-800 font-bold px-2 py-0.5 rounded text-[11px]">
                              Richiesta colloquio inoltrata!
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-slate-800 pt-1">
                          <div>Domanda singola: <strong>{chk.domanda_singola} / 5</strong></div>
                          {chk.bat12_punteggio && (
                            <div>Media BAT-12: <strong className="text-rose-600">{chk.bat12_punteggio} / 5</strong></div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* FORM PRESA IN CARICO */}
              <div className="bg-primary-50/50 p-4 rounded-xl border border-primary-200">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
                  <UserCheck className="w-4 h-4 text-primary-700" />
                  <span>Gestione Presa in Carico (Alimenta il contatore direzionale HR)</span>
                </h3>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Stato della Presa in Carico:</label>
                    <select
                      value={presaInCaricoStato}
                      onChange={(e) => setPresaInCaricoStato(e.target.value)}
                      className="border border-slate-300 rounded-lg p-2 bg-white text-slate-800 font-medium w-full sm:w-60 focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="contattato">Contattato</option>
                      <option value="in_valutazione">In Valutazione Clinica</option>
                      <option value="concluso">Concluso / Risolto</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-700 mb-1">Note Cliniche Riservate (Non visibili all'HR):</label>
                    <textarea
                      rows={3}
                      value={presaInCaricoNote}
                      onChange={(e) => setPresaInCaricoNote(e.target.value)}
                      placeholder="Note confidenziali sul colloquio, piano di rientro turni o prescrizioni..."
                      className="border border-slate-300 rounded-lg p-2.5 bg-white text-slate-800 w-full focus:ring-2 focus:ring-primary-500"
                    />
                  </div>

                  {feedbackSalvataggio && (
                    <div className="bg-emerald-100 text-emerald-800 p-2.5 rounded-lg flex items-center gap-2 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span>{feedbackSalvataggio}</span>
                    </div>
                  )}

                  <div className="pt-2 text-right">
                    <button
                      onClick={handleSalvaPresaInCarico}
                      className="bg-primary-600 hover:bg-primary-700 text-white font-semibold px-4 py-2 rounded-xl transition-colors shadow-sm"
                    >
                      Salva Presa in Carico
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AUDIT LOG MODAL */}
      {showAuditLogs && (
        <AuditLogModal logs={auditLogs} onClose={() => setShowAuditLogs(false)} />
      )}
    </div>
  );
};
