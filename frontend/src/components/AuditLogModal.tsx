import React from 'react';
import { AuditLogEntry } from '../types';
import { ShieldCheck, X, Clock, UserCheck } from 'lucide-react';

interface AuditLogModalProps {
  logs: AuditLogEntry[];
  onClose: () => void;
}

export const AuditLogModal: React.FC<AuditLogModalProps> = ({ logs, onClose }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl max-w-3xl w-full shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2 text-slate-900 font-bold">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <span>Registro di Controllo degli Accessi (Audit Trail GDPR)</span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Info */}
        <div className="px-5 py-3 bg-emerald-50/50 border-b border-emerald-100 text-xs text-emerald-800">
          A norma degli artt. 9, 32 e 88 del GDPR, ogni visualizzazione di schede clinico-organizzative individuali viene tracciata in modo indelebile con data, utente e causale.
        </div>

        {/* Table Content */}
        <div className="p-5 overflow-y-auto flex-1">
          {logs.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">Nessun record di audit presente.</div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase">
                  <th className="py-2.5 px-3">Data e Ora</th>
                  <th className="py-2.5 px-3">Utente / Ruolo</th>
                  <th className="py-2.5 px-3">Azione</th>
                  <th className="py-2.5 px-3">Codice Operatore</th>
                  <th className="py-2.5 px-3">Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80">
                    <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleString('it-IT')}
                    </td>
                    <td className="py-2.5 px-3 font-medium text-slate-800">
                      {log.utente_id} <span className="text-slate-400">({log.ruolo})</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-700 font-semibold">{log.azione.replace('_', ' ')}</td>
                    <td className="py-2.5 px-3 font-mono text-primary-700">{log.target_codice || '-'}</td>
                    <td className="py-2.5 px-3 text-slate-500">{log.note || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 text-white rounded-xl text-xs font-semibold hover:bg-slate-900 transition-colors"
          >
            Chiudi Registro
          </button>
        </div>
      </div>
    </div>
  );
};
