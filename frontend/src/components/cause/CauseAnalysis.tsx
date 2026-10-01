import { FC, useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { Dossier, Incident } from '../../types/api';
import { CheckCircle2, Network } from 'lucide-react';

interface CauseAnalysisProps {
  dossier: Dossier | null;
  incident: Incident | null;
}

export const CauseAnalysis: FC<CauseAnalysisProps> = ({ dossier }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // GSAP animation for hypothesis probability bars
  useGSAP(
    () => {
      if (!dossier || dossier.ranked.length === 0) return;
      gsap.from('.prob-fill', {
        scaleX: 0,
        transformOrigin: 'left center',
        duration: 0.8,
        stagger: 0.1,
        ease: 'power2.out',
      });
    },
    { dependencies: [dossier], scope: containerRef }
  );

  if (!dossier) {
    return (
      <div className="border-2 border-black bg-surface p-12 text-center space-y-3">
        <h2 className="font-serif italic text-2xl font-bold text-black">
          Autonomous Bayesian Diagnostic Standby
        </h2>
        <p className="text-sm text-textMuted max-w-lg mx-auto">
          The multi-agent diagnostic engine cross-examines KSNDMC rainfall radars, elevation slopes, ticket timeline lags, and TomTom traffic congestion. Load the Bellandur flood scenario to inspect full Bayesian posteriors.
        </p>
      </div>
    );
  }

  const hypothesisNames: Record<string, string> = {
    POWER_LED_STP_OVERFLOW: '⚡ Substation Power Outage Halting BWSSB STP Pumping Stations',
    RAIN_OVERWHELM: '🌧️ Extreme Cloudburst Runoff Overwhelming Rajakaluve Canal Capacity',
    DRAIN_BLOCKAGE: '🧱 Primary Stormwater Culvert Silt & Solid Waste Obstruction',
    PIPE_BURST: '🚰 BWSSB High-Pressure Water Supply Main Burst',
    LAKE_OVERFLOW: '🌊 Bellandur Lake Weir Breach & Upstream Backflow Inundation',
    TRAFFIC_ONLY: '🚗 Arterial Bottleneck Stagnation Without Active Flooding',
    power_led_stp: '⚡ Substation Power Outage Halting BWSSB STP Pumping Stations',
    rain_overwhelm: '🌧️ Extreme Cloudburst Runoff Overwhelming Rajakaluve Canal Capacity',
    culvert_blockage: '🧱 Primary Stormwater Culvert Silt & Solid Waste Obstruction',
  };

  const getProvenanceBadge = (prov: string) => {
    switch (prov.toLowerCase()) {
      case 'real':
        return 'bg-black text-white border-black font-bold';
      case 'simulated':
        return 'bg-bone text-black border-black font-bold';
      case 'derived':
      default:
        return 'bg-white text-black border-borderDark font-medium';
    }
  };

  const leadingHypothesis = dossier.ranked[0];
  const isPowerLedStp = leadingHypothesis && leadingHypothesis[0].includes('STP');

  return (
    <div ref={containerRef} className="space-y-6">
      {/* Overview Header */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-borderSubtle pb-4">
          <div>
            <span className="text-[11px] font-mono uppercase text-textMuted tracking-wider block font-bold">
              Autonomous Root Cause Diagnostics
            </span>
            <h2 className="text-2xl md:text-3xl font-serif font-bold italic text-black tracking-tight mt-1 max-w-5xl">
              Bayesian Hypothesis Ranking & Multi-Source Signals
            </h2>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-mono border-2 border-black bg-bone px-3 py-1 font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-black" />
              STATUS: {dossier.conclusive ? 'CONCLUSIVE' : 'EVALUATING'}
            </span>
          </div>
        </div>
        <p className="text-sm text-textBody leading-relaxed max-w-4xl">
          Diagnostic conclusion: <strong>{dossier.stop_reason}</strong>. Public sensor readings, ticket timelines, and municipal feeds have been weighted into closed-form posterior log-odds.
        </p>
      </div>

      {/* Connecting the Dots Deep Architectural Breakdown */}
      {isPowerLedStp && (
        <div className="border-2 border-black bg-bone p-6 md:p-8 space-y-3">
          <div className="flex items-center gap-2 text-black font-serif font-bold italic text-lg">
            <Network className="w-5 h-5 text-black" />
            <span>How NammaTwin Connected the Dots Across Siloed Agencies</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono pt-2">
            <div className="border border-black bg-white p-3 space-y-1">
              <span className="font-bold text-black uppercase block">1. BESCOM Power Signal</span>
              <p className="text-textMuted">
                5 complaints regarding Kadubeesanahalli Substation sparking and 11kV Feeder F-KADU-04 trip recorded at 07:10 UTC.
              </p>
            </div>
            <div className="border border-black bg-white p-3 space-y-1">
              <span className="font-bold text-black uppercase block">2. Spatiotemporal Lag (45m)</span>
              <p className="text-textMuted">
                Sewage and floodwater overflow tickets on ORR began precisely 45 minutes later as STP wet well overflowed without pump power.
              </p>
            </div>
            <div className="border border-black bg-white p-3 space-y-1">
              <span className="font-bold text-black uppercase block">3. Multi-Agency Joint Action</span>
              <p className="text-textMuted">
                Dispatches BESCOM breaker crew to restore power (P1) AND BWSSB suction machines (P1) simultaneously, avoiding 6h misdirected dewatering.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Hypothesis Probability Bars */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-borderSubtle pb-3">
          <h3 className="font-serif font-bold italic text-lg text-black">
            Ranked Hypotheses
          </h3>
          <span className="text-xs font-mono text-textMuted">Bayesian Posterior Confidence</span>
        </div>

        <div className="space-y-5">
          {dossier.ranked.map(([hypId, prob], index) => {
            const percentage = Math.round(prob * 100);
            const isLeading = index === 0;
            return (
              <div key={hypId} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold border border-black px-1.5 py-0.5 bg-white">
                      #{index + 1}
                    </span>
                    <span className={`font-serif ${isLeading ? 'font-bold italic text-black text-base' : 'text-textBody'}`}>
                      {hypothesisNames[hypId] || hypId}
                    </span>
                  </div>
                  <span className="font-mono text-sm font-bold text-black">{percentage}%</span>
                </div>

                {/* GSAP Animated Probability Bar */}
                <div className="h-4 border border-black bg-bone w-full relative overflow-hidden">
                  <div
                    className={`prob-fill h-full ${isLeading ? 'bg-black' : 'bg-[#57606A]'}`}
                    style={{ width: `${Math.max(percentage, 2)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Verified Evidence Table with Provenance Badges */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        <div className="flex items-center justify-between border-b border-borderSubtle pb-3">
          <h3 className="font-serif font-bold italic text-lg text-black">
            Multi-Source Evidence Chain & Provenance Audit
          </h3>
          <span className="text-xs font-mono text-textMuted">{dossier.evidence.length} empirical signals</span>
        </div>

        <div className="divide-y divide-borderSubtle">
          {dossier.evidence.map((ev) => (
            <div key={ev.id} className="py-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold uppercase text-black">
                    🛠️ {ev.tool} TOOL
                  </span>
                  <span className="text-xs font-mono text-textMuted">({ev.source})</span>
                </div>
                <span className={`font-mono text-[10px] uppercase px-2 py-0.5 border ${getProvenanceBadge(ev.provenance)}`}>
                  [{ev.provenance}]
                </span>
              </div>
              <p className="text-sm text-textBody">{ev.summary}</p>
              {ev.keys && ev.keys.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {ev.keys.map((k) => (
                    <span key={k} className="text-[10px] font-mono bg-bone border border-borderDark px-1.5 py-0.5">
                      {k}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Execution Trace */}
      {dossier.trace && dossier.trace.length > 0 && (
        <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-3">
          <h3 className="font-serif font-bold italic text-base text-black">
            🔍 LangGraph Investigator Step-by-Step Reasoning Trace ({dossier.trace.length} Steps)
          </h3>
          <div className="space-y-2 text-xs font-mono">
            {dossier.trace.map((step: any, idx) => (
              <div key={idx} className="border border-borderDark p-2.5 bg-bone flex flex-col gap-1">
                <div className="flex justify-between font-bold text-black">
                  <span>Step {step.step || idx + 1}: Tool `{step.tool}`</span>
                  <span>Posterior: {step.top_hypothesis || 'POWER_LED_STP_OVERFLOW'}</span>
                </div>
                <div className="text-textMuted">{step.why || 'Discriminative tool choice based on prior distribution'}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
