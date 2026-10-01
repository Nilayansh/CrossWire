import { FC } from 'react';
import { Incident } from '../../types/api';

interface HeaderNavProps {
  activeStage: 1 | 2 | 3 | 4;
  onSelectStage: (stage: 1 | 2 | 3 | 4) => void;
  incident: Incident | null;
}

export const HeaderNav: FC<HeaderNavProps> = ({
  activeStage,
  onSelectStage,
  incident,
}) => {
  const stages = [
    { id: 1 as const, name: 'Citizen Reports' },
    { id: 2 as const, name: 'Flood Basin Map' },
    { id: 3 as const, name: 'Cause Analysis' },
    { id: 4 as const, name: 'Dispatch Console' },
  ];

  const getStatusBadge = () => {
    if (!incident) return { label: 'STANDBY', bg: 'bg-bone text-textMuted border-borderSubtle' };
    switch (incident.status) {
      case 'dispatched':
        return { label: 'DISPATCHED', bg: 'bg-black text-white border-black' };
      case 'awaiting_approval':
        return { label: 'URGENT ACTION', bg: 'bg-black text-white border-black' };
      case 'closed':
        return { label: 'RESOLVED', bg: 'bg-white text-black border-black' };
      default:
        return { label: incident.status.toUpperCase(), bg: 'bg-bone text-black border-black' };
    }
  };

  const status = getStatusBadge();

  return (
    <header className="sticky top-0 z-50 bg-[#FBFBF9]/95 backdrop-blur-md border-b-2 border-black">
      {/* Top Project Bar */}
      <div className="max-w-6xl mx-auto px-6 py-2.5 flex items-center justify-between border-b border-borderSubtle">
        <div className="flex items-center gap-3">
          <img
            src="/assets/vidhana_soudha_crest.svg"
            alt="Vidhana Soudha Crest"
            className="w-6 h-6 object-contain"
            onError={(e) => {
              // Graceful fallback if asset fails to load
              e.currentTarget.style.display = 'none';
            }}
          />
          <span className="text-xl font-serif font-bold italic tracking-tight text-textMain">
            CrossWire
          </span>
          <span className="hidden sm:inline-block text-xs text-textMuted border-l border-borderSubtle pl-3 font-sans">
            Bengaluru Incident Intelligence
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          {incident && (
            <div className="border border-borderDark px-2.5 py-1 bg-bone flex items-center gap-1.5">
              <span className="w-2 h-2 bg-red-600 rounded-full animate-ping" />
              <span className="font-bold text-black">{incident.id}</span>
              <span className="text-textMuted hidden md:inline">({incident.cells.length} hex cells)</span>
            </div>
          )}
          <div className={`border-2 px-2.5 py-1 font-bold text-[11px] uppercase tracking-wider ${status.bg}`}>
            {status.label}
          </div>
        </div>
      </div>

      {/* 4-Stage Sequential Navigation */}
      <nav className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm overflow-x-auto">
        <div className="flex items-center gap-2 md:gap-4 py-2">
          {stages.map((s) => {
            const isActive = activeStage === s.id;
            return (
              <button
                key={s.id}
                onClick={() => onSelectStage(s.id)}
                className={`px-3 py-1 flex items-center gap-2 border-b-2 font-serif transition-all duration-150 ${
                  isActive
                    ? 'border-black font-bold italic text-black'
                    : 'border-transparent text-textMuted hover:text-black font-medium'
                }`}
              >
                <span
                  className={`font-mono text-xs w-4 h-4 flex items-center justify-center not-italic border ${
                    isActive ? 'border-black bg-white font-bold' : 'border-borderSubtle text-textMuted'
                  }`}
                >
                  {s.id}
                </span>
                <span>{s.name}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </header>
  );
};
