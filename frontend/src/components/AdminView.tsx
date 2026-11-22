import React, { useState } from 'react';
import { api } from '../services/api';
import { IngestReportResponse } from '../types';
import { Upload, Download, Sparkles, CheckCircle2, AlertTriangle, ShieldCheck, FileSpreadsheet, RefreshCw } from 'lucide-react';

export const AdminView: React.FC = () => {
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [demoSuccess, setDemoSuccess] = useState<string | null>(null);
  const [uploadReport, setUploadReport] = useState<IngestReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleLoadDemo = async () => {
    try {
      setLoadingDemo(true);
      setError(null);
      const res = await api.loadDemo();
      setDemoSuccess(res.messaggio || 'Clinica demo caricata con successo (150 dipendenti, 6 reparti, 24 mesi).');
      setUploadReport(null);
    } catch (err: any) {
      setError(err.message || 'Errore nel caricamento della clinica demo');
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setError(null);
      setDemoSuccess(null);
      const report = await api.uploadExcel(file);
      setUploadReport(report);
    } catch (err: any) {
      setError(err.message || 'Errore durante l\'importazione del file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-6">
      {/* Intro Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Caricamento Dati & Ingestione</h1>
          <p className="text-sm text-slate-500 mt-1">
            Gestisci l'importazione sicura dei fogli Excel o avvia istantaneamente la clinica demo di prova.
          </p>
        </div>
        <button
          onClick={handleLoadDemo}
          disabled={loadingDemo}
          className="flex items-center gap-2 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-sm transition-all disabled:opacity-50"
        >
          {loadingDemo ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          <span>{loadingDemo ? 'Caricamento in corso...' : '⚡ Carica Clinica Demo'}</span>
        </button>
      </div>

      {/* Notifications */}
      {demoSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl flex items-center gap-3 text-emerald-800 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{demoSuccess} Ora puoi esplorare la <strong>Vista HR</strong> e la <strong>Vista Medico</strong> con dati realistici!</span>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl flex items-center gap-3 text-rose-800 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid: Upload & Privacy Guarantees */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upload Excel Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 text-slate-900 font-bold mb-2">
              <FileSpreadsheet className="w-5 h-5 text-primary-600" />
              <h2>Carica File Excel Clinica</h2>
            </div>
            <p className="text-xs text-slate-500 mb-6 leading-relaxed">
              Carica il file Excel unico contenente i 7 fogli: <code className="text-slate-700 font-mono">dipendenti</code>, <code className="text-slate-700 font-mono">turni</code>, <code className="text-slate-700 font-mono">assenze</code>, <code className="text-slate-700 font-mono">ore_mese</code>, <code className="text-slate-700 font-mono">eventi_hr</code>, <code className="text-slate-700 font-mono">aggressioni</code>, <code className="text-slate-700 font-mono">occupazione</code>.
            </p>

            <label className="border-2 border-dashed border-slate-300 hover:border-primary-500 rounded-2xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-primary-50/20">
              <Upload className="w-8 h-8 text-slate-400 mb-2" />
              <span className="text-sm font-semibold text-slate-700">
                {uploading ? 'Elaborazione e pseudonimizzazione...' : 'Clicca per selezionare il file Excel'}
              </span>
              <span className="text-xs text-slate-400 mt-1">Formati ammessi: .xlsx, .xls</span>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Mapping matricola → codice:</span>
            <a
              href={api.getDownloadMappingUrl()}
              className="text-primary-600 hover:text-primary-700 font-semibold flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Scarica CSV (solo Medico/Admin)</span>
            </a>
          </div>
        </div>

        {/* Privacy by Design Banner */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-6 rounded-2xl shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 font-bold mb-3 text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
              <h2>Privacy by Design & GDPR</h2>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed mb-4">
              I dati dei lavoratori sanitari sono protetti da rigorosi vincoli legali e tecnologici:
            </p>

            <ul className="space-y-3 text-xs text-slate-300">
              <li className="flex items-start gap-2">
                <span className="bg-emerald-500/20 text-emerald-300 p-0.5 rounded font-bold">✓</span>
                <span><strong>Pseudonimizzazione HMAC all'istante:</strong> la matricola diventa un hash di 10 caratteri all'import e non viene mai registrata nel DB.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-emerald-500/20 text-emerald-300 p-0.5 rounded font-bold">✓</span>
                <span><strong>Whitelist rigida dei campi:</strong> nomi, codici fiscali e diagnosi cliniche vengono scartati preventivamente.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-emerald-500/20 text-emerald-300 p-0.5 rounded font-bold">✓</span>
                <span><strong>K-Anonymity (K = 6):</strong> le viste aggregate non mostrano mai reparti con meno di 6 individui.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="bg-emerald-500/20 text-emerald-300 p-0.5 rounded font-bold">✓</span>
                <span><strong>Separazione Ruoli:</strong> l'HR non ha mai visibilità su dati sanitari o check-in dei singoli.</span>
              </li>
            </ul>
          </div>

          <div className="mt-6 text-[11px] text-slate-400 bg-slate-800/80 p-3 rounded-xl border border-slate-700">
            Conforme a GDPR art. 9 (dati particolari), art. 88 (lavoro) e Statuto dei Lavoratori (L. 300/1970 art. 4).
          </div>
        </div>
      </div>

      {/* Validation Report if present */}
      {uploadReport && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>Report di Validazione Importazione ({uploadReport.filename})</span>
          </h3>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {Object.entries(uploadReport.righe_accettate).map(([foglio, count]) => (
              <div key={foglio} className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-xs text-slate-500 capitalize">{foglio}</div>
                <div className="text-lg font-bold text-slate-800 mt-0.5">{count} righe</div>
              </div>
            ))}
          </div>

          {Object.keys(uploadReport.colonne_ignorate).length > 0 && (
            <div className="text-xs text-amber-700 bg-amber-50 p-3 rounded-xl border border-amber-200">
              <strong>Colonne non autorizzate scartate all'origine:</strong>
              <ul className="list-disc pl-5 mt-1 space-y-0.5">
                {Object.entries(uploadReport.colonne_ignorate).map(([f, cols]) => (
                  <li key={f}>Foglio <em>{f}</em>: {cols.join(', ')}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
