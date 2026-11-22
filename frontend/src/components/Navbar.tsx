import React from 'react';
import { UserRole } from '../types';
import { Shield, BarChart3, Stethoscope, User, Database, HeartPulse } from 'lucide-react';

interface NavbarProps {
  currentRole: UserRole;
  onRoleChange: (role: UserRole) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentRole, onRoleChange }) => {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Brand */}
          <div className="flex items-center gap-3">
            <div className="bg-primary-600 text-white p-2 rounded-xl shadow-sm">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
                Libellula <span className="text-xs uppercase bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-semibold">PoC Sanità</span>
              </span>
              <p className="text-xs text-slate-500 font-medium">Prevenzione Rischio Burnout & Privacy by Design</p>
            </div>
          </div>

          {/* Role Navigation Pills */}
          <nav className="flex items-center bg-slate-100 p-1.5 rounded-xl border border-slate-200 gap-1">
            <button
              onClick={() => onRoleChange('admin')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                currentRole === 'admin'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Dati & Import</span>
            </button>

            <button
              onClick={() => onRoleChange('hr')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                currentRole === 'hr'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Vista HR</span>
            </button>

            <button
              onClick={() => onRoleChange('medico')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                currentRole === 'medico'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <Stethoscope className="w-3.5 h-3.5" />
              <span>Vista Medico</span>
            </button>

            <button
              onClick={() => onRoleChange('lavoratore')}
              className={`flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                currentRole === 'lavoratore'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/50'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Vista Lavoratore</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
};
