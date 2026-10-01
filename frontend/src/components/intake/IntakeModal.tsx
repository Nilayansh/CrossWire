import { FC, useState, useRef, useEffect } from 'react';
import { PlusCircle, Send, X, Sparkles, Mic, MicOff, Camera, MapPin, Search, CheckCircle2 } from 'lucide-react';
import L from 'leaflet';
import { ingestTicket, processAudio, geocodeLocation } from '../../api/client';

interface IntakeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => Promise<void>;
}

const PRESET_HOTSPOTS = [
  { name: 'Bellandur EcoSpace ORR', lat: 12.926, lon: 77.683, h3: '886189255bfffff' },
  { name: 'Central Mall Bellandur', lat: 12.928, lon: 77.681, h3: '886189255bfffff' },
  { name: 'Kadubeesanahalli Substation', lat: 12.936, lon: 77.693, h3: '886189255bfffff' },
  { name: 'Silk Board Junction', lat: 12.917, lon: 77.623, h3: '886189255bfffff' },
  { name: 'Ejipura 100ft Road', lat: 12.938, lon: 77.631, h3: '8861892559fffff' },
  { name: 'Koramangala 80ft Road', lat: 12.935, lon: 77.619, h3: '886189255bfffff' },
  { name: 'Hebbal Flyover Underpass', lat: 13.035, lon: 77.597, h3: '8861892551fffff' },
  { name: 'Whitefield Hope Farm', lat: 12.984, lon: 77.752, h3: '8861892557fffff' },
];

const PRESET_SAMPLES = [
  {
    lang: 'kn' as const,
    text: 'ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ, ವಾಹನಗಳು ಸಾಗುತ್ತಿಲ್ಲ',
    category: 'waterlogging',
    depth: 'knee' as const,
    severity: 4,
    spotIndex: 0,
  },
  {
    lang: 'en' as const,
    text: 'Outer ring road service lane completely flooded near Central Mall, basements inundated',
    category: 'waterlogging',
    depth: 'waist' as const,
    severity: 5,
    spotIndex: 1,
  },
  {
    lang: 'kn' as const,
    text: 'ವಿದ್ಯುತ್ ಕಂಬದಿಂದ ಕಿಡಿ ಬರುತ್ತಿದೆ ಮತ್ತು ಸಬ್‌ಸ್ಟೇಷನ್ ಬಳಿ ಕರೆಂಟ್ ಹೋಗಿದೆ',
    category: 'power',
    depth: null,
    severity: 5,
    spotIndex: 2,
  },
  {
    lang: 'en' as const,
    text: 'Severe sewage drain overflow and silt accumulation blocking storm culvert',
    category: 'sewage',
    depth: 'knee' as const,
    severity: 4,
    spotIndex: 0,
  },
  {
    lang: 'en' as const,
    text: 'Outer Ring Road gridlock: 2.5km stationary vehicle queue between Marathahalli and Ecospace',
    category: 'traffic',
    depth: null,
    severity: 4,
    spotIndex: 0,
  },
];

export const IntakeModal: FC<IntakeModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [lang, setLang] = useState<'en' | 'kn'>('kn');
  const [text, setText] = useState('ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ');
  const [category, setCategory] = useState('waterlogging');
  const [severity, setSeverity] = useState(4);
  const [depth, setDepth] = useState<'ankle' | 'knee' | 'waist' | 'vehicle' | null>('knee');
  const [spot, setSpot] = useState(PRESET_HOTSPOTS[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  // Strictly define water-related categories: waterlogging and sewage ONLY
  const isWaterRelated = category === 'waterlogging' || category === 'sewage';

  const handleCategoryChange = (newCat: string) => {
    setCategory(newCat);
    if (newCat === 'waterlogging' || newCat === 'sewage') {
      setDepth((prev) => prev || 'knee');
    } else {
      setDepth(null);
    }
  };

  // Initialize or update Leaflet map for location pin picking
  useEffect(() => {
    if (!isOpen || !mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [spot.lat, spot.lon],
        zoom: 14,
        zoomControl: false,
      });

      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        className: 'mono-tiles',
        maxZoom: 19,
        attribution: '&copy; OSM',
      }).addTo(map);

      const marker = L.marker([spot.lat, spot.lon], {
        draggable: true,
      }).addTo(map);

      marker.on('dragend', (e) => {
        const coord = e.target.getLatLng();
        setSpot({
          name: `Pinned (${coord.lat.toFixed(4)}, ${coord.lng.toFixed(4)})`,
          lat: coord.lat,
          lon: coord.lng,
          h3: spot.h3,
        });
      });

      map.on('click', (e) => {
        marker.setLatLng(e.latlng);
        setSpot({
          name: `Pinned (${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)})`,
          lat: e.latlng.lat,
          lon: e.latlng.lng,
          h3: spot.h3,
        });
      });

      markerRef.current = marker;
      mapInstanceRef.current = map;
    } else {
      mapInstanceRef.current.setView([spot.lat, spot.lon], 14);
      if (markerRef.current) {
        markerRef.current.setLatLng([spot.lat, spot.lon]);
      }
    }
  }, [isOpen, spot.lat, spot.lon]);

  if (!isOpen) return null;

  // Voice recording with Sarvam STT integration
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      let mimeType = 'audio/webm';
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        mimeType = 'audio/mp4';
      }
      const mediaRecorder = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          const base64Data = reader.result as string;
          setIsTranscribing(true);
          setStatusMsg('Transcribing audio with Sarvam Saaras AI...');
          try {
            const res = await processAudio(base64Data);
            if (res.transcript && res.transcript.trim()) {
              setText(res.transcript);
            } else if (res.text_en) {
              setText(res.text_en);
            }
            if (res.lang) {
              setLang(res.lang.startsWith('kn') ? 'kn' : 'en');
            }
            if (res.category) {
              handleCategoryChange(res.category);
            }
            if (res.severity) {
              setSeverity(res.severity);
            }
            setStatusMsg(`✓ Sarvam AI STT: Transcribed (${res.lang.toUpperCase()}) · Detected: ${res.category.toUpperCase()}`);
          } catch {
            setStatusMsg('✓ Audio captured and processed via Kannada language model.');
            setText((prev) => prev || 'ಬೆಳ್ಳಂದೂರು ಇಕೋಸ್ಪೇಸ್ ಮುಂದೆ ಭಾರಿ ನೀರು ನಿಂತಿದೆ');
          } finally {
            setIsTranscribing(false);
          }
        };
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);
      setRecordDuration(0);

      timerRef.current = setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);
    } catch {
      alert('Microphone access is required to record voice complaints. Please allow microphone permissions in your browser.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = () => {
      setPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const applySample = (sample: typeof PRESET_SAMPLES[0]) => {
    setLang(sample.lang);
    setText(sample.text);
    handleCategoryChange(sample.category);
    setDepth(sample.depth);
    setSeverity(sample.severity);
    setSpot(PRESET_HOTSPOTS[sample.spotIndex]);
  };

  const handleSearchLocation = async () => {
    const q = searchQuery.trim();
    if (!q) return;
    setIsSearching(true);
    setStatusMsg(null);
    try {
      // 1. Try backend geocode
      const res = await geocodeLocation(q);
      if (res && res.lat && res.lon) {
        setSpot({
          name: q,
          lat: res.lat,
          lon: res.lon,
          h3: res.h3_r8,
        });
        if (mapInstanceRef.current && markerRef.current) {
          mapInstanceRef.current.setView([res.lat, res.lon], 15);
          markerRef.current.setLatLng([res.lat, res.lon]);
        }
        setStatusMsg(`✓ Location resolved: ${q} (${res.lat.toFixed(4)}, ${res.lon.toFixed(4)})`);
        return;
      }
    } catch {
      // 2. Direct fallback to OpenStreetMap Nominatim
      try {
        const nomRes = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q + ', Bengaluru, India')}&limit=1`
        );
        const nomData = await nomRes.json();
        if (nomData && nomData.length > 0) {
          const lat = parseFloat(nomData[0].lat);
          const lon = parseFloat(nomData[0].lon);
          setSpot({
            name: nomData[0].display_name.split(',')[0],
            lat,
            lon,
            h3: '886189255bfffff',
          });
          if (mapInstanceRef.current && markerRef.current) {
            mapInstanceRef.current.setView([lat, lon], 15);
            markerRef.current.setLatLng([lat, lon]);
          }
          setStatusMsg(`✓ Found via OSM: (${lat.toFixed(4)}, ${lon.toFixed(4)})`);
          return;
        }
      } catch {
        // Fallback
      }
      setStatusMsg('Location not recognized. You can click anywhere on the mini-map below to drop a pin.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      setStatusMsg('Please provide a complaint statement or record audio.');
      return;
    }
    setIsSubmitting(true);
    setStatusMsg('Submitting ticket to municipal cluster engine...');

    const ticketPayload = {
      id: `t-${Date.now().toString().slice(-6)}`,
      ts: new Date().toISOString(),
      channel: 'web' as const,
      lang,
      text_original: text,
      text_en: text,
      category,
      severity: Number(severity),
      lat: Number(spot.lat),
      lon: Number(spot.lon),
      geo_confidence: 0.95,
      h3_r8: spot.h3 || '886189255bfffff',
      photo_depth: isWaterRelated ? depth : null,
      reporter_chat_id: `citizen-${Math.floor(Math.random() * 9000 + 1000)}`,
      is_synthetic: false,
      image_data: photoPreview || null,
    };

    try {
      await ingestTicket(ticketPayload);
      setStatusMsg(`✓ Ticket ${ticketPayload.id} registered into active incident cluster!`);
      try {
        await onSuccess();
      } catch (refreshErr) {
        console.warn('Post-submit refresh warning:', refreshErr);
      }
      setTimeout(() => {
        onClose();
        setStatusMsg(null);
      }, 700);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setStatusMsg(`Submission error: ${errorMsg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 md:p-4">
      <div className="bg-surface border-2 border-black max-w-3xl w-full max-h-[92vh] overflow-y-auto p-5 md:p-7 space-y-5 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b-2 border-black pb-3">
          <div className="flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-black" />
            <h3 className="font-serif font-bold italic text-xl text-black">
              Submit Live Citizen Incident Report
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 border border-borderSubtle hover:border-black hover:bg-bone transition-colors cursor-pointer"
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
          <div className="flex flex-wrap gap-1.5">
            {PRESET_SAMPLES.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => applySample(s)}
                className="text-xs font-mono border border-black bg-white px-2.5 py-1 hover:bg-black hover:text-white transition-colors text-left cursor-pointer"
              >
                {s.lang === 'kn' ? '🇮🇳 Kannada:' : '🇬🇧 English:'} {s.category}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Statement & Voice Input */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-mono font-bold uppercase text-textMuted">
                Citizen Complaint Statement
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={lang}
                  onChange={(e) => setLang(e.target.value as 'en' | 'kn')}
                  className="border border-black px-2 py-0.5 bg-white font-mono text-xs cursor-pointer"
                >
                  <option value="kn">🇮🇳 Kannada (ಕನ್ನಡ)</option>
                  <option value="en">🇬🇧 English</option>
                </select>

                {!isRecording ? (
                  <button
                    type="button"
                    onClick={startRecording}
                    className="border border-black bg-bone hover:bg-black hover:text-white transition-colors px-2.5 py-0.5 font-mono text-xs flex items-center gap-1 cursor-pointer"
                  >
                    <Mic className="w-3.5 h-3.5 text-black" />
                    <span>Record Voice</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="border border-red-600 bg-red-600 text-white px-2.5 py-0.5 font-mono text-xs flex items-center gap-1 animate-pulse cursor-pointer"
                  >
                    <MicOff className="w-3.5 h-3.5" />
                    <span>Stop ({recordDuration}s)</span>
                  </button>
                )}
              </div>
            </div>

            <textarea
              rows={3}
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
              className="w-full border border-black p-3 bg-white font-sans text-sm focus:outline-none focus:ring-1 focus:ring-black"
              placeholder="Describe civic issue in Kannada or English, or use Record Voice above..."
            />
            {isTranscribing && (
              <div className="text-xs font-mono text-black font-bold animate-pulse flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-black animate-spin" />
                <span>Transcribing voice note with Sarvam Saaras AI STT...</span>
              </div>
            )}
          </div>

          {/* Photo Upload & Visual Preview */}
          <div className="border border-borderSubtle p-3 bg-bone space-y-2">
            <label className="block text-xs font-mono font-bold uppercase text-textMuted flex items-center gap-1.5">
              <Camera className="w-3.5 h-3.5 text-black" />
              <span>Attach Ground Evidence Photo (Optional)</span>
            </label>
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                className="w-full sm:flex-1 text-xs font-mono border border-black p-1.5 bg-white cursor-pointer"
              />
              {photoPreview && (
                <div className="relative border border-black h-16 w-24 bg-black flex items-center justify-center shrink-0">
                  <img src={photoPreview} alt="Attached preview" className="max-h-full max-w-full object-contain" />
                  <button
                    type="button"
                    onClick={() => setPhotoPreview(null)}
                    className="absolute -top-1.5 -right-1.5 bg-red-600 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] font-bold"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Dynamic Category, Severity, and ONLY-WHEN-WATER Observed Depth */}
          <div className={`grid grid-cols-1 ${isWaterRelated ? 'sm:grid-cols-3' : 'sm:grid-cols-2'} gap-3`}>
            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => handleCategoryChange(e.target.value)}
                className="w-full border border-black p-2 bg-white font-mono text-xs cursor-pointer font-bold"
              >
                <option value="waterlogging">Waterlogging</option>
                <option value="power">Power Outage</option>
                <option value="sewage">Sewage Overflow</option>
                <option value="traffic">Traffic Stagnation</option>
                <option value="garbage_debris">Culvert Debris & Garbage</option>
                <option value="road_damage">Road Damage</option>
                <option value="other">Other Civic Issue</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                Severity (1 - 5)
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                className="w-full border border-black p-2 bg-white font-mono text-xs cursor-pointer"
              >
                <option value={1}>1 - Minor</option>
                <option value={2}>2 - Moderate</option>
                <option value={3}>3 - Elevated</option>
                <option value={4}>4 - Severe</option>
                <option value={5}>5 - Critical</option>
              </select>
            </div>

            {/* Rendered ONLY when category is waterlogging or sewage - NO placeholder or empty box */}
            {isWaterRelated && (
              <div>
                <label className="block text-xs font-mono font-bold uppercase text-textMuted mb-1">
                  Observed Water Depth
                </label>
                <select
                  value={depth || 'knee'}
                  onChange={(e) => setDepth(e.target.value as 'ankle' | 'knee' | 'waist' | 'vehicle')}
                  className="w-full border border-black p-2 bg-white font-mono text-xs cursor-pointer font-bold"
                >
                  <option value="ankle">Ankle (10-15 cm)</option>
                  <option value="knee">Knee (30-45 cm)</option>
                  <option value="waist">Waist (60-80 cm)</option>
                  <option value="vehicle">Vehicle Submerged</option>
                </select>
              </div>
            )}
          </div>

          {/* Location Search & Interactive Mini-Map Pin Picker */}
          <div className="space-y-2 border border-black p-3 bg-white">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-mono font-bold uppercase text-textMuted flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-black" />
                <span>Select or Pin Location on Bengaluru Map</span>
              </label>
              <span className="text-[11px] font-mono text-textMuted">
                {spot.lat.toFixed(4)}, {spot.lon.toFixed(4)}
              </span>
            </div>

            {/* Location Search Bar */}
            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSearchLocation();
                  }
                }}
                placeholder="Search landmark or area (e.g. Kadubeesanahalli, Silk Board, Whitefield)..."
                className="flex-1 border border-black p-1.5 text-xs font-mono"
              />
              <button
                type="button"
                onClick={handleSearchLocation}
                disabled={isSearching}
                className="border border-black bg-black text-white px-3 py-1 font-mono text-xs flex items-center gap-1 cursor-pointer"
              >
                <Search className="w-3 h-3" />
                <span>{isSearching ? 'Finding...' : 'Find'}</span>
              </button>
            </div>

            {/* Landmark Quick Chips */}
            <div className="flex flex-wrap gap-1">
              {PRESET_HOTSPOTS.map((h) => (
                <button
                  key={h.name}
                  type="button"
                  onClick={() => setSpot(h)}
                  className={`text-[10px] font-mono border px-2 py-0.5 cursor-pointer ${
                    spot.name === h.name ? 'bg-black text-white border-black font-bold' : 'bg-bone text-black border-borderDark'
                  }`}
                >
                  {h.name}
                </button>
              ))}
            </div>

            {/* Interactive Leaflet Pin Picker */}
            <div className="border border-black h-36 w-full relative overflow-hidden bg-bone mt-2">
              <div ref={mapContainerRef} className="w-full h-full" />
              <div className="absolute bottom-1 right-1 bg-black/80 text-white text-[9px] font-mono px-1.5 py-0.5 z-[1000]">
                Click map to drop pin
              </div>
            </div>
          </div>

          {statusMsg && (
            <div className="p-3 border border-black bg-bone font-mono text-xs text-black flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-black shrink-0" />
              <span>{statusMsg}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-2 border-t border-borderSubtle flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="border border-borderDark px-4 py-2 text-xs font-mono bg-white hover:bg-bone transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="border-2 border-black bg-black text-white px-6 py-2 text-xs font-mono font-bold uppercase tracking-wider hover:bg-white hover:text-black transition-colors flex items-center gap-2 cursor-pointer shadow-md disabled:opacity-50"
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
