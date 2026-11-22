import React, { useState } from 'react';
import { api } from '../services/api';
import { LavoratoreStatoResponse } from '../types';
import {
  User,
  HeartPulse,
  Send,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Lock,
  MessageSquare,
  Sparkles,
} from 'lucide-react';

const BAT_QUESTIONS = [
  "Al lavoro mi sento mentalmente esausto/a.",
  "Tutto ciò che faccio al lavoro mi richiede uno sforzo estremo.",
  "Mi sento fisicamente svuotato/a al termine della giornata lavorativa.",
  "Al mattino, quando mi alzo, non mi sento riposato/a per iniziare il lavoro.",
  "Faccio fatica a trovare entusiasmo per la mia attività quotidiana.",
  "Sento una forte distanza mentale o distacco emotivo verso il lavoro.",
  "Sono diventato/a più cinico/a o disilluso/a riguardo al mio lavoro.",
  "Al lavoro ho difficoltà a concentrarmi e a mantenere l'attenzione.",
  "Mi capita di commettere errori o dimenticanze per distrazione.",
  "Faccio fatica a pensare con lucidità mentre lavoro.",
  "Al lavoro mi capita di perdere la calma o sentirmi irritabile.",
  "Mi capita di sentirmi sopraffatto/a dall'ansia o dalle emozioni al lavoro.",
];

export const LavoratoreView: React.FC = () => {
  const [codiceInput, setCodiceInput] = useState<string>('');
  const [lavoratoreStato, setLavoratoreStato] = useState<LavoratoreStatoResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Check-in Form State
  const [domandaSingola, setDomandaSingola] = useState<number>(2);
  const [batRisposte, setBatRisposte] = useState<number[]>(Array(12).fill(2));
  const [consensoMedico, setConsensoMedico] = useState<boolean>(true);
  const [richiestaColloquio, setRichiestaColloquio] = useState<boolean>(false);
  const [sendingCheckin, setSendingCheckin] = useState<boolean>(false);
  const [checkinSuccessMsg, setCheckinSuccessMsg] = useState<string | null>(null);

  const handleAccedi = async (cod?: string) => {
    const codDaUsare = (cod || codiceInput).trim();
    if (!codDaUsare) {
      setError('Inserisci il tuo codice pseudonimo');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setCheckinSuccessMsg(null);
      await api.accessoCodice(codDaUsare);
      const stato = await api.getMioStato(codDaUsare);
      setLavoratoreStato(stato);
      setCodiceInput(codDaUsare);
    } catch (err: any) {
      setError(err.message || 'Codice non riconosciuto nel sistema');
    } finally {
      setLoading(false);
    }
  };

  const handleInviaCheckin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lavoratoreStato) return;

    try {
      setSendingCheckin(true);
      setCheckinSuccessMsg(null);
      const payload = {
        codice: lavoratoreStato.codice,
        domanda_singola: domandaSingola,
        bat12_risposte: domandaSingola >= 3 ? batRisposte : undefined,
        consenso_medico: consensoMedico,
        richiesta_colloquio: richiestaColloquio,
      };

      const res = await api.inviaCheckin(payload);
      setCheckinSuccessMsg(res.messaggio_feed);
      // Ricarica stato lavoratore aggiornato
      const updatedStato = await api.getMioStato(lavoratoreStato.codice);
      setLavoratoreStato(updatedStato);
    } catch (err: any) {
      alert('Errore invio check-in: ' + err.message);
    } finally {
      setSendingCheckin(false);
    }
  };

  const handleToggleConsenso = async () => {
    if (!lavoratoreStato) return;
    const nuovoStato = !lavoratoreStato.consenso_medico_attivo;
    try {
      await api.updateConsenso(lavoratoreStato.codice, nuovoStato);
      setLavoratoreStato({
        ...lavoratoreStato,
        consenso_medico_attivo: nuovoStato,
      });
      alert(nuovoStato ? 'Consenso attivato con successo.' : 'Consenso revocato. Il medico non vedrà più i tuoi check-in.');
    } catch (err: any) {
      alert('Errore aggiornamento consenso: ' + err.message);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto py-6">
      {/* Box Accesso Codice se non ancora autenticato */}
      {!lavoratoreStato ? (
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm max-w-lg mx-auto text-center space-y-6">
          <div className="bg-primary-50 text-primary-600 w-12 h-12 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
            <User className="w-6 h-6" />
          </div>

          <div>
            <h1 className="text-2xl font-bold text-slate-900">Spazio Personale Lavoratore</h1>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Inserisci il tuo codice pseudonimo per accedere al check-in mensile e verificare il tuo stato di benessere lavorativo.
            </p>
          </div>

          {error && (
            <div className="bg-rose-50 border border-rose-200 p-3 rounded-xl text-rose-800 text-xs">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={codiceInput}
              onChange={(e) => setCodiceInput(e.target.value)}
              placeholder="Es. codice a 10 caratteri..."
              className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm font-mono focus:ring-2 focus:ring-primary-500 focus:outline-none"
            />
            <button
              onClick={() => handleAccedi()}
              disabled={loading}
              className="bg-primary-600 hover:bg-primary-700 text-white px-5 py-2.5 rounded-xl font-semibold text-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Accesso...' : 'Entra'}
            </button>
          </div>

          {/* Quick Demo Helper */}
          <div className="pt-4 border-t border-slate-100 text-xs text-slate-400">
            <span>Per provare la demo, carica prima la demo in <strong>Dati & Import</strong> oppure seleziona un codice dalla <strong>Vista Medico</strong>.</span>
          </div>
        </div>
      ) : (
        /* SCHEDA LAVORATORE AUTENTICATO */
        <div className="space-y-6">
          {/* Header Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs bg-primary-100 text-primary-800 font-bold px-2.5 py-0.5 rounded-md">
                  Area Riservata
                </span>
                <h1 className="text-lg font-bold text-slate-900 font-mono">Codice: {lavoratoreStato.codice}</h1>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Reparto: <strong>{lavoratoreStato.reparto}</strong> | Ruolo: <strong>{lavoratoreStato.ruolo}</strong>
              </p>
            </div>

            <button
              onClick={() => setLavoratoreStato(null)}
              className="text-xs text-slate-500 hover:text-slate-800 border border-slate-200 px-3 py-1.5 rounded-lg hover:bg-slate-50"
            >
              Cambia Codice
            </button>
          </div>

          {/* Card Esito e Spiegazione Semplice */}
          <div className="bg-gradient-to-r from-primary-50 to-indigo-50 border border-primary-200 p-6 rounded-2xl shadow-sm">
            <div className="flex items-start gap-4">
              <div className="bg-white p-3 rounded-2xl shadow-sm text-primary-600 flex-shrink-0">
                <HeartPulse className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-slate-900">Il Tuo Quadro di Benessere Lavorativo</h2>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full uppercase ${
                    lavoratoreStato.fascia === 'alto'
                      ? 'bg-rose-100 text-rose-800'
                      : lavoratoreStato.fascia === 'medio'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {lavoratoreStato.fascia}
                  </span>
                </div>
                <p className="text-xs text-slate-700 leading-relaxed pt-1">
                  {lavoratoreStato.spiegazione}
                </p>
              </div>
            </div>
          </div>

          {/* Form Check-in Mensile */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-primary-600" />
                <span>Check-in Mensile di Benessere</span>
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                La compilazione richiede meno di 1 minuto. Le tue risposte sono riservate e protette dal segreto professionale.
              </p>
            </div>

            {checkinSuccessMsg && (
              <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>{checkinSuccessMsg}</span>
              </div>
            )}

            <form onSubmit={handleInviaCheckin} className="space-y-6">
              {/* STEP 1: Domanda Singola */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
                <label className="block text-sm font-bold text-slate-900">
                  1. Nelle ultime settimane, quanto ti sei sentito/a emotivamente sopraffatto/a o svuotato/a dal lavoro?
                </label>
                <div className="grid grid-cols-5 gap-2 text-center text-xs">
                  {[
                    { val: 1, label: 'Mai' },
                    { val: 2, label: 'Raramente' },
                    { val: 3, label: 'Talvolta' },
                    { val: 4, label: 'Spesso' },
                    { val: 5, label: 'Sempre' },
                  ].map((item) => (
                    <button
                      type="button"
                      key={item.val}
                      onClick={() => setDomandaSingola(item.val)}
                      className={`p-3 rounded-xl border transition-all font-semibold ${
                        domandaSingola === item.val
                          ? 'bg-primary-600 text-white border-primary-600 shadow-sm'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-primary-400'
                      }`}
                    >
                      <div className="text-base font-extrabold">{item.val}</div>
                      <div className="text-[11px] mt-0.5">{item.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* STEP 2: Sblocco BAT-12 se domanda >= 3 */}
              {domandaSingola >= 3 && (
                <div className="p-5 rounded-2xl border-2 border-primary-200 bg-primary-50/40 space-y-4 animate-fadeIn">
                  <div className="flex items-center gap-2 text-primary-900 font-bold text-sm">
                    <Sparkles className="w-4 h-4 text-primary-600" />
                    <span>Approfondimento Consigliato: Questionario BAT-12 (Burnout Assessment Tool)</span>
                  </div>
                  <p className="text-xs text-primary-800">
                    Avendo indicato un livello di affaticamento significativo, rispondi a queste 12 brevi domande per consentire una valutazione mirata.
                  </p>

                  <div className="space-y-3">
                    {BAT_QUESTIONS.map((q, idx) => (
                      <div key={idx} className="bg-white p-3 rounded-xl border border-slate-200 text-xs">
                        <div className="font-medium text-slate-800 mb-2">{idx + 1}. {q}</div>
                        <div className="flex gap-2">
                          {[1, 2, 3, 4, 5].map((num) => (
                            <button
                              type="button"
                              key={num}
                              onClick={() => {
                                const newRisp = [...batRisposte];
                                newRisp[idx] = num;
                                setBatRisposte(newRisp);
                              }}
                              className={`flex-1 py-1 rounded-lg text-xs font-semibold border ${
                                batRisposte[idx] === num
                                  ? 'bg-primary-600 text-white border-primary-600'
                                  : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                              }`}
                            >
                              {num}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* STEP 3: Consenso e Richiesta Colloquio */}
              <div className="space-y-3 pt-2 text-xs">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={consensoMedico}
                    onChange={(e) => setConsensoMedico(e.target.checked)}
                    className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  />
                  <span className="font-medium text-slate-700">
                    Condividi in modo confidenziale il risultato con il Medico Competente / Psicologo aziendale (revocabile in ogni momento)
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer bg-rose-50/60 p-3 rounded-xl border border-rose-200">
                  <input
                    type="checkbox"
                    checked={richiestaColloquio}
                    onChange={(e) => setRichiestaColloquio(e.target.checked)}
                    className="w-4 h-4 text-rose-600 rounded focus:ring-rose-500"
                  />
                  <span className="font-semibold text-rose-900">
                    Desidero richiedere un colloquio clinico riservato con il Medico Competente
                  </span>
                </label>
              </div>

              <div className="text-right pt-3">
                <button
                  type="submit"
                  disabled={sendingCheckin}
                  className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-colors shadow-sm disabled:opacity-50 inline-flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  <span>{sendingCheckin ? 'Invio in corso...' : 'Invia Check-in'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Privacy & Revoca Consenso Box */}
          <div className="bg-slate-100 p-5 rounded-2xl border border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs">
            <div className="space-y-1">
              <div className="font-bold text-slate-800 flex items-center gap-1.5">
                <Lock className="w-4 h-4 text-slate-500" />
                <span>Controllo e Sovranità sul Consenso (GDPR)</span>
              </div>
              <p className="text-slate-500">
                Stato attuale: <strong>{lavoratoreStato.consenso_medico_attivo ? 'Condivisione Attiva' : 'Condivisione Revocata'}</strong>. Il datore di lavoro e l'HR non possono mai vedere il tuo profilo.
              </p>
            </div>

            <button
              onClick={handleToggleConsenso}
              className={`px-4 py-2 rounded-xl font-semibold transition-colors ${
                lavoratoreStato.consenso_medico_attivo
                  ? 'bg-rose-100 text-rose-800 hover:bg-rose-200'
                  : 'bg-emerald-600 text-white hover:bg-emerald-700'
              }`}
            >
              {lavoratoreStato.consenso_medico_attivo ? 'Revoca Consenso Medico' : 'Attiva Consenso Medico'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
