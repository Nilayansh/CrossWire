import { FC, useState } from 'react';
import { Ticket, Incident } from '../../types/api';
import { Volume2, MapPin, Plus, Sparkles } from 'lucide-react';

interface CitizenReportsProps {
  tickets: Ticket[];
  incident: Incident | null;
  onOpenIntake: () => void;
  onLoadScenario: () => Promise<void>;
}

export const CitizenReports: FC<CitizenReportsProps> = ({
  tickets,
  incident,
  onOpenIntake,
  onLoadScenario,
}) => {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const playVoice = (text: string, lang: string) => {
    if ('speechSynthesis' in window) {
      if (isPlayingAudio) {
        window.speechSynthesis.cancel();
        setIsPlayingAudio(false);
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang === 'kn' ? 'kn-IN' : 'en-IN';
      utterance.rate = 0.95;
      utterance.onstart = () => setIsPlayingAudio(true);
      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsPlayingAudio(!isPlayingAudio);
    }
  };

  if (!incident || tickets.length === 0) {
    return (
      <div className="border-2 border-black bg-surface p-12 text-center space-y-6">
        <div className="w-12 h-12 border-2 border-black bg-bone flex items-center justify-center mx-auto">
          <MapPin className="w-6 h-6 text-black" />
        </div>
        <div className="space-y-2">
          <h2 className="font-serif italic text-2xl font-bold text-black">
            Incident Command Standby
          </h2>
          <p className="text-sm text-textMuted max-w-lg mx-auto">
            No active emergency complaints in the database. Submit a live citizen complaint or inject a Bangalore flood cluster to run the multi-agent diagnostic pipeline.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={onOpenIntake}
            className="border-2 border-black bg-black text-white px-6 py-2.5 font-mono text-xs font-bold uppercase tracking-wider hover:bg-white hover:text-black transition-colors flex items-center gap-2 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            + Submit New Citizen Report
          </button>
          <button
            onClick={onLoadScenario}
            className="border-2 border-black bg-bone hover:bg-black hover:text-white transition-colors px-6 py-2.5 font-mono text-xs font-bold flex items-center gap-2 cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            Load Bellandur Flood Cluster (17 Reports)
          </button>
        </div>
      </div>
    );
  }

  const primaryTicket = tickets[0];
  const secondaryTickets = tickets.slice(1);

  return (
    <div className="space-y-8">
      {/* Hero Summary Card */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-borderSubtle pb-4">
          <div>
            <span className="text-[11px] font-mono uppercase text-textMuted tracking-wider block font-bold">
              Active Incident Cluster
            </span>
            <h1 className="text-2xl md:text-3xl font-serif font-bold italic text-textMain tracking-tight mt-1 max-w-5xl">
              {incident.id}: {primaryTicket.text_en || primaryTicket.text_original}
            </h1>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onOpenIntake}
              className="border-2 border-black bg-black text-white px-3 py-1 text-xs font-mono font-bold uppercase hover:bg-white hover:text-black transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Report</span>
            </button>
            <span className="text-xs font-mono border-2 border-black bg-bone px-3 py-1 font-bold">
              {tickets.length} REPORTS
            </span>
          </div>
        </div>
        <p className="text-sm text-textBody leading-relaxed max-w-4xl">
          Unified telemetry clustering citizen helpline tickets across H3 spatial hexagonal cells. Speech statements, geocoded coordinates, and photo depth readings are verified below.
        </p>
      </div>

      {/* Bento Grid with grid-flow-dense */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 grid-flow-dense">
        {/* Primary Citizen Report with Audio Statement */}
        <div className="col-span-12 md:col-span-8 border-2 border-black bg-surface p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-borderSubtle pb-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold bg-bone border border-black px-2 py-0.5">
                {primaryTicket.id}
              </span>
              <span className="text-xs font-mono text-textMuted uppercase">
                {primaryTicket.channel} · {new Date(primaryTicket.ts).toLocaleTimeString()}
              </span>
            </div>
            {primaryTicket.photo_depth && (
              <span className="font-mono text-xs font-bold border border-black bg-black text-white px-2.5 py-0.5">
                DEPTH: {primaryTicket.photo_depth.toUpperCase()}
              </span>
            )}
          </div>

          {/* Photo & Kannada Audio Statement */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border border-black bg-bone relative overflow-hidden group">
              <img
                src="/assets/bangalore_flood_incident.jpg"
                alt="Flood depth observation at Bellandur"
                className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
              <div className="absolute bottom-2 left-2 right-2 bg-black/80 text-white p-2 text-[11px] font-mono flex items-center justify-between">
                <span>Visual Depth Estimate</span>
                <span className="font-bold">{primaryTicket.photo_depth ? primaryTicket.photo_depth.toUpperCase() : '45 - 60 cm'}</span>
              </div>
            </div>

            <div className="border border-black bg-bone p-4 space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs font-mono font-bold">
                    <Volume2 className="w-4 h-4 text-black" />
                    <span>Sarvam Kannada STT</span>
                  </div>
                  <button
                    onClick={() => playVoice(primaryTicket.text_original, primaryTicket.lang)}
                    className="text-xs font-mono border border-black px-2.5 py-1 bg-white hover:bg-black hover:text-white transition-colors cursor-pointer"
                  >
                    {isPlayingAudio ? '⏹ Stop Voice' : '▶ Play Voice Audio'}
                  </button>
                </div>
                <div className="bg-white border border-borderSubtle p-2.5 space-y-1">
                  <div className="text-[10px] font-mono text-textMuted">Original ({primaryTicket.lang.toUpperCase()}):</div>
                  <p className="text-xs font-medium text-black leading-relaxed">
                    "{primaryTicket.text_original}"
                  </p>
                  {primaryTicket.lang !== 'en' && (
                    <>
                      <div className="text-[10px] font-mono text-textMuted pt-1">Verified English Translation:</div>
                      <p className="text-xs text-textBody italic font-serif">
                        "{primaryTicket.text_en}"
                      </p>
                    </>
                  )}
                </div>
              </div>

              <div className="text-[11px] font-mono text-textMuted flex items-center justify-between border-t border-borderSubtle pt-2">
                <span>Geo Confidence</span>
                <span className="font-bold text-black">{Math.round(primaryTicket.geo_confidence * 100)}%</span>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-textMuted pt-2 border-t border-borderSubtle">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-black" />
              {primaryTicket.lat.toFixed(4)}, {primaryTicket.lon.toFixed(4)}
            </span>
            <span>H3: {primaryTicket.h3_r8}</span>
            <span className="text-black font-bold">Severity: {primaryTicket.severity}/5</span>
            <span className="text-black font-bold capitalize">Category: {primaryTicket.category}</span>
          </div>
        </div>

        {/* Secondary Report Stream Column */}
        <div className="col-span-12 md:col-span-4 border-2 border-black bg-surface p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderSubtle pb-2">
            <h3 className="font-serif font-bold italic text-base text-black">
              Corroborating Reports
            </h3>
            <span className="text-xs font-mono text-textMuted">{secondaryTickets.length} queued</span>
          </div>

          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {secondaryTickets.length === 0 ? (
              <div className="text-xs text-textMuted italic py-4 text-center">
                No additional queued reports in this cluster yet.
              </div>
            ) : (
              secondaryTickets.map((t) => (
                <div key={t.id} className="border border-borderSubtle p-3 space-y-1 bg-bone">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="font-bold text-black">{t.id}</span>
                    <span className="text-textMuted">{new Date(t.ts).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-xs text-textBody line-clamp-2">
                    {t.text_en || t.text_original}
                  </p>
                  <div className="flex items-center justify-between text-[10px] font-mono text-textMuted pt-1">
                    <span className="capitalize">{t.category}</span>
                    {t.photo_depth && (
                      <span className="border border-black bg-white px-1 font-bold text-black">
                        {t.photo_depth.toUpperCase()}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
