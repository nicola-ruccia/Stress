import React, { useState } from 'react';
import { UserRole } from './types';
import { Navbar } from './components/Navbar';
import { AdminView } from './components/AdminView';
import { HRView } from './components/HRView';
import { MedicoView } from './components/MedicoView';
import { LavoratoreView } from './components/LavoratoreView';
import { Shield, HeartHandshake } from 'lucide-react';

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<UserRole>('hr');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col justify-between">
      <div>
        <Navbar currentRole={currentRole} onRoleChange={setCurrentRole} />

        <main className="px-4 sm:px-6 lg:px-8 py-6">
          {currentRole === 'admin' && <AdminView />}
          {currentRole === 'hr' && <HRView />}
          {currentRole === 'medico' && <MedicoView />}
          {currentRole === 'lavoratore' && <LavoratoreView />}
        </main>
      </div>

      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-slate-500 font-medium">
            <HeartHandshake className="w-4 h-4 text-primary-600" />
            <span>Libellula - PoC Rischio Burnout in Sanità Privata</span>
          </div>

          <div className="flex items-center gap-4 text-slate-400">
            <span>Conforme a GDPR Artt. 9 e 88</span>
            <span>•</span>
            <span>Validazione INAIL & BAT-12</span>
            <span>•</span>
            <span>Privacy by Design & K_MIN = 6</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
