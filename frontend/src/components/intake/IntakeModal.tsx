import { FC, useState } from 'react';
import { PlusCircle, Send, X, Sparkles } from 'lucide-react';
import { ingestTicket } from '../../api/client';

interface IntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => Promise<void>;
}

const PRESET_HOTSPOTS = [
  { name: 'Bellandur EcoSpace ORR', lat: 12.926, lon: 77.683, h3: '886189255bfffff' },
  { name: 'Silk Board Junction', lat: 12.917, lon: 77.623, h3: '886189255bfffff' },
  { name: 'Ejipura 100ft Road', lat: 12.938, lon: 77.631, h3: '8861892559fffff' },
  { name: 'Koramangala 80ft Road', lat: 12.935, lon: 77.619, h3: '886189255bfffff' },
  { name: 'Hebbal Flyover Underpass', lat: 13.035, lon: 77.597, h3: '8861892551fffff' },
];

const PRESET_SAMPLES = [
  {
    lang: 'kn',
    text: 'ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ, ವಾಹನಗಳು ಸಾಗುತ್ತಿಲ್ಲ',
    category: 'waterlogging',
    depth: 'knee' as const,
    severity: 4,
    spotIndex: 0,
  },
  {
    lang: 'en',
    text: 'Outer ring road service lane completely flooded near Central Mall, water entering basements',
    category: 'waterlogging',
    depth: 'waist' as const,
    severity: 5,
    spotIndex: 0,
  },
  {
    lang: 'en',
    text: 'Transformer spark and total power blackout at pump station near Koramangala',
    category: 'power',
    depth: 'ankle' as const,
    severity: 4,
    spotIndex: 3,
  },
  {
    lang: 'en',
    text: 'Severe sewage drain overflow and silt accumulation blocking storm culvert',
    category: 'sewage',
    depth: 'knee' as const,
    severity: 4,
    spotIndex: 2,
  },
];

export const IntakeModal: FC<IntakeModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [lang, setLang] = useState<'en' | 'kn'>('kn');
  const [text, setText] = useState('ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ');
  const [category, setCategory] = useState('waterlogging');
  const [severity, setSeverity] = useState(4);
  const [depth, setDepth] = useState<'ankle' | 'knee' | 'waist' | 'vehicle'>('knee');
  const [spot, setSpot] = useState(PRESET_HOTSPOTS[0]);
  const [channel, setChannel] = useState<'telegram' | 'web'>('telegram');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const applySample = (sample: typeof PRESET_SAMPLES[0]) => {
    setLang(sample.lang as 'en' | 'kn');
    setText(sample.text);
    setCategory(sample.category);
    setDepth(sample.depth);
    setSeverity(sample.severity);
    setSpot(PRESET_HOTSPOTS[sample.spotIndex]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setStatusMsg(null);

    const ticketPayload = {
      id: `t-${Date.now().toString().slice(-6)}`,
      ts: new Date().toISOString(),
      channel,
      lang,
      text_original: text,
      text_en: text, // Backend translation adapter handles Kannada automatically
      category,
      severity: Number(severity),
      lat: spot.lat,
      lon: spot.lon,
      geo_confidence: 0.95,
      h3_r8: spot.h3,
      photo_depth: depth,
      reporter_chat_id: `user-${Math.floor(Math.random() * 9000 + 1000)}`,
      is_synthetic: false,
    };

    try {
      const res = await ingestTicket(ticketPayload);
      setStatusMsg(`Success! Ticket ingested (${ticketPayload.id}) -> Incident: ${res.incident_id || 'clustered'}`);
      await onSuccess();
      setTimeout(() => {
        onClose();
        setStatusMsg(null);
      }, 1200);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setStatusMsg(`Error ingesting ticket: ${errorMsg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-surface border-2 border-black max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 md:p-8 space-y-6 shadow-2xl">
        <div className="flex items-center justify-between border-b-2 border-black pb-3">
          <div className="flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-black" />
            <h3 className="font-serif font-bold italic text-xl text-black">
              Submit Live Citizen Incident Report
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 border border-borderSubtle hover:border-black hover:bg-bone transition-colors"
          >
            <X className="w-5 h-5 text-black" />
          </button>
        </div>

        {/* Quick Sample Presets */}
        <div className="space-y-2 bg-bone border border-borderSubtle p-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-textMuted font-bold">
            <Sparkles className="w-3.5 h-3.5 text-black" />
            <span>Quick-Fill Live Complaint Templates:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {PRESET_SAMPLES.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => applySample(s)}
                className="text-xs font-mono border border-black bg-white px-2.5 py-1 hover:bg-black hover:text-white transition-colors text-left"
              >
                {s.lang === 'kn' ? '🇮🇳 Kannada:' : '🇬🇧 English:'} {s.category} ({s.depth})
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Input Language
              </label>
              <select
                value={lang}
                onChange={(e) => setLang(e.target.value as 'en' | 'kn')}
                className="w-full border border-black p-2 bg-white font-mono text-sm"
              >
                <option value="kn">Kannada (ಕನ್ನಡ)</option>
                <option value="en">English</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Intake Channel
              </label>
              <select
                value={channel}
                onChange={(e) => setChannel(e.target.value as 'telegram' | 'web')}
                className="w-full border border-black p-2 bg-white font-mono text-sm"
              >
                <option value="telegram">Telegram Helpline (112 / BBMP Bot)</option>
                <option value="web">Web Portal Citizen Desk</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
              Citizen Complaint Statement
            </label>
            <textarea
              rows={3}
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
              className="w-full border border-black p-3 bg-white font-sans text-sm focus:outline-none focus:ring-1 focus:ring-black"
              placeholder="Enter citizen description in Kannada or English..."
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full border border-black p-2 bg-white font-mono text-xs"
              >
                <option value="waterlogging">Waterlogging</option>
                <option value="power">Power Outage</option>
                <option value="sewage">Sewage Overflow</option>
                <option value="traffic">Traffic Stagnation</option>
                <option value="solid_waste">Culvert Debris</option>
                <option value="road_damage">Road Damage</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Severity (1 - 5)
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                className="w-full border border-black p-2 bg-white font-mono text-xs"
              >
                <option value={1}>1 - Minor</option>
                <option value={2}>2 - Moderate</option>
                <option value={3}>3 - Elevated</option>
                <option value={4}>4 - Severe</option>
                <option value={5}>5 - Critical</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Observed Water Depth
              </label>
              <select
                value={depth}
                onChange={(e) => setDepth(e.target.value as 'ankle' | 'knee' | 'waist' | 'vehicle')}
                className="w-full border border-black p-2 bg-white font-mono text-xs"
              >
                <option value="ankle">Ankle (10-15 cm)</option>
                <option value="knee">Knee (30-45 cm)</option>
                <option value="waist">Waist (60-80 cm)</option>
                <option value="vehicle">Vehicle Submerged</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
              Bangalore Location / Coordinates
            </label>
            <select
              value={spot.name}
              onChange={(e) => {
                const s = PRESET_HOTSPOTS.find((h) => h.name === e.target.value);
                if (s) setSpot(s);
              }}
              className="w-full border border-black p-2 bg-white font-mono text-xs mb-2"
            >
              {PRESET_HOTSPOTS.map((h) => (
                <option key={h.name} value={h.name}>
                  {h.name} ({h.lat}, {h.lon})
                </option>
              ))}
            </select>
            <div className="text-[11px] font-mono text-textMuted flex items-center justify-between">
              <span>Lat: {spot.lat.toFixed(4)}, Lon: {spot.lon.toFixed(4)}</span>
              <span>H3 Cell: {spot.h3}</span>
            </div>
          </div>

          {statusMsg && (
            <div className="p-3 border border-black bg-bone font-mono text-xs text-black">
              {statusMsg}
            </div>
          )}

          <div className="pt-3 border-t border-borderSubtle flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="border border-borderDark px-4 py-2 text-xs font-mono bg-white hover:bg-bone transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="border-2 border-black bg-black text-white px-6 py-2 text-xs font-mono font-bold uppercase tracking-wider hover:bg-white hover:text-black transition-colors flex items-center gap-2 cursor-pointer"
            >
              <Send className="w-4 h-4" />
              {isSubmitting ? 'Ingesting...' : 'Submit to Live Backend (POST /tickets)'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
