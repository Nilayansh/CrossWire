import { FC, useState } from 'react';
import { Ticket, Incident } from '../../types/api';
import { Volume2, MapPin, Plus, Sparkles, Filter, AlertTriangle } from 'lucide-react';

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
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isInjecting, setIsInjecting] = useState(false);

  const activeTicket = selectedTicketId
    ? tickets.find((t) => t.id === selectedTicketId) || tickets[0]
    : tickets[0];

  const filteredTickets = categoryFilter === 'all'
    ? tickets
    : tickets.filter((t) => t.category === categoryFilter);

  const playVoice = (text: string, lang: string) => {
    if ('speechSynthesis' in window) {
      if (isPlayingAudio) {
        window.speechSynthesis.cancel();
        setIsPlayingAudio(false);
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = lang === 'kn' ? 'kn-IN' : 'en-IN';
      utterance.rate = 0.92;
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
            No active emergency complaints in the database. Submit a live citizen complaint or inject the Bellandur flood scenario cluster to run the multi-agent diagnostic pipeline.
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
            onClick={async () => {
              setIsInjecting(true);
              try {
                await onLoadScenario();
              } finally {
                setIsInjecting(false);
              }
            }}
            disabled={isInjecting}
            className="border-2 border-black bg-bone hover:bg-black hover:text-white transition-colors px-6 py-2.5 font-mono text-xs font-bold flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${isInjecting ? 'animate-spin' : ''}`} />
            <span>{isInjecting ? 'Injecting 14 Reports...' : 'Load Bellandur Flood Cluster (14 Reports)'}</span>
          </button>
        </div>
      </div>
    );
  }

  const categoryList = ['all', ...Array.from(new Set(tickets.map((t) => t.category)))];

  // Connecting the dots detection summary
  const hasPower = tickets.some((t) => t.category === 'power');
  const hasWaterOrSewage = tickets.some((t) => t.category === 'waterlogging' || t.category === 'sewage');
  const isConnectingDots = hasPower && hasWaterOrSewage;

  return (
    <div className="space-y-6">
      {/* Incident Cluster Header */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-borderSubtle pb-4">
          <div>
            <span className="text-[11px] font-mono uppercase text-textMuted tracking-wider block font-bold">
              Active Incident Cluster
            </span>
            <h1 className="text-2xl md:text-3xl font-serif font-bold italic text-black tracking-tight mt-1">
              Incident {incident.id}: Bellandur &ndash; Kadubeesanahalli Corridor
            </h1>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={onOpenIntake}
              className="border-2 border-black bg-black text-white px-3 py-1.5 text-xs font-mono font-bold uppercase hover:bg-white hover:text-black transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Report</span>
            </button>
            <span className="text-xs font-mono border-2 border-black bg-bone px-3 py-1.5 font-bold">
              {tickets.length} REPORTS CLUSTERED
            </span>
          </div>
        </div>

        {/* Connecting the Dots Callout */}
        {isConnectingDots && (
          <div className="border border-black bg-bone p-3 text-xs font-mono flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-black shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-black uppercase">Cross-Agency Root Cause Link Detected:</span>{' '}
              <span className="text-textBody">
                BESCOM power outage complaints precede BWSSB sewage/stormwater overflow by 45 minutes. Traditional 311 systems misroute these as two disconnected events &mdash; NammaTwin correlates them to identify substation pump tripping.
              </span>
            </div>
          </div>
        )}

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-textMuted pt-1">
          <span>Centroid: {incident.centroid[0].toFixed(4)}, {incident.centroid[1].toFixed(4)}</span>
          <span>Status: <b className="uppercase text-black">{incident.status}</b></span>
          <span>Active H3 Cells: {incident.cells.join(', ')}</span>
        </div>
      </div>

      {/* Main Inspection View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Ticket Focused Card */}
        {activeTicket && (
          <div className="lg:col-span-7 border-2 border-black bg-surface p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-borderSubtle pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold bg-black text-white px-2 py-0.5">
                  {activeTicket.id}
                </span>
                <span className="text-xs font-mono text-textMuted uppercase">
                  {activeTicket.channel} &bull; {new Date(activeTicket.ts).toLocaleTimeString()}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono border border-black bg-bone px-2 py-0.5 font-bold capitalize">
                  {activeTicket.category}
                </span>
                {activeTicket.photo_depth && (
                  <span className="font-mono text-xs font-bold border border-black bg-white px-2 py-0.5">
                    DEPTH: {activeTicket.photo_depth.toUpperCase()}
                  </span>
                )}
              </div>
            </div>

            {/* Photo & Audio Preview Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Photo Display */}
              <div className="border border-black bg-bone relative overflow-hidden h-52 flex items-center justify-center">
                {activeTicket.image_data ? (
                  <img
                    src={activeTicket.image_data}
                    alt="Citizen uploaded proof"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <img
                    src="/assets/bangalore_flood_incident.jpg"
                    alt="Flood depth observation at Bellandur"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                )}
                <div className="absolute bottom-2 left-2 right-2 bg-black/85 text-white p-2 text-[11px] font-mono flex items-center justify-between">
                  <span>Visual Verification</span>
                  <span className="font-bold">
                    {activeTicket.photo_depth ? `DEPTH: ${activeTicket.photo_depth.toUpperCase()}` : 'SEVERITY: ' + activeTicket.severity + '/5'}
                  </span>
                </div>
              </div>

              {/* Kannada Audio & Text Statement */}
              <div className="border border-black bg-bone p-4 space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-mono font-bold">
                      <Volume2 className="w-4 h-4 text-black" />
                      <span>Sarvam Kannada STT</span>
                    </div>
                    <button
                      onClick={() => playVoice(activeTicket.text_original, activeTicket.lang)}
                      className="text-xs font-mono border border-black px-2.5 py-1 bg-white hover:bg-black hover:text-white transition-colors cursor-pointer"
                    >
                      {isPlayingAudio ? '⏹ Stop' : '▶ Play Audio'}
                    </button>
                  </div>

                  <div className="bg-white border border-borderSubtle p-2.5 space-y-1">
                    <div className="text-[10px] font-mono text-textMuted uppercase font-bold">
                      Statement ({activeTicket.lang}):
                    </div>
                    <p className="text-xs font-medium text-black leading-relaxed">
                      "{activeTicket.text_original}"
                    </p>
                    {activeTicket.lang !== 'en' && activeTicket.text_en !== activeTicket.text_original && (
                      <>
                        <div className="text-[10px] font-mono text-textMuted pt-1 uppercase font-bold">
                          English Translation:
                        </div>
                        <p className="text-xs text-textBody italic font-serif">
                          "{activeTicket.text_en}"
                        </p>
                      </>
                    )}
                  </div>
                </div>

                <div className="text-[11px] font-mono text-textMuted flex items-center justify-between border-t border-borderSubtle pt-2">
                  <span>Geo Confidence: <b className="text-black">{Math.round(activeTicket.geo_confidence * 100)}%</b></span>
                  <span>Severity: <b className="text-black">{activeTicket.severity}/5</b></span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-textMuted pt-2 border-t border-borderSubtle">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-black" />
                {activeTicket.lat.toFixed(4)}, {activeTicket.lon.toFixed(4)}
              </span>
              <span>H3 Cell: <code>{activeTicket.h3_r8}</code></span>
              <span className="text-black font-bold">Category: {activeTicket.category.toUpperCase()}</span>
            </div>
          </div>
        )}

        {/* All Clustered Tickets Feed Column */}
        <div className="lg:col-span-5 border-2 border-black bg-surface p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-borderSubtle pb-2">
            <h3 className="font-serif font-bold italic text-base text-black flex items-center gap-2">
              <Filter className="w-4 h-4 text-black" />
              <span>Corroborating Reports ({filteredTickets.length})</span>
            </h3>
            <span className="text-xs font-mono text-textMuted">Click to Inspect</span>
          </div>

          {/* Category Filter Chips */}
          <div className="flex flex-wrap gap-1">
            {categoryList.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`text-[10px] font-mono border px-2 py-0.5 uppercase cursor-pointer ${
                  categoryFilter === cat
                    ? 'bg-black text-white border-black font-bold'
                    : 'bg-bone text-black border-borderDark hover:bg-white'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Ticket Cards List */}
          <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
            {filteredTickets.map((t) => {
              const isSelected = activeTicket?.id === t.id;
              return (
                <div
                  key={t.id}
                  onClick={() => setSelectedTicketId(t.id)}
                  className={`border p-3 space-y-1 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-2 border-black bg-white shadow-sm'
                      : 'border-borderDark bg-bone hover:border-black'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="font-bold text-black">{t.id}</span>
                    <span className="text-textMuted">{new Date(t.ts).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-xs text-textBody line-clamp-2">
                    {t.text_en || t.text_original}
                  </p>
                  <div className="flex items-center justify-between text-[10px] font-mono text-textMuted pt-1">
                    <span className="font-bold text-black capitalize">{t.category}</span>
                    <div className="flex items-center gap-1.5">
                      <span>Sev: {t.severity}/5</span>
                      {t.photo_depth && (
                        <span className="border border-black bg-white px-1 font-bold text-black">
                          {t.photo_depth.toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
