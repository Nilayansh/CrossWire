import { FC, useRef } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import { Dossier, Incident } from '../../types/api';

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
        stagger: 0.12,
        ease: 'power2.out',
      });
    },
    { dependencies: [dossier], scope: containerRef }
  );

  if (!dossier) {
    return (
      <div className="border-2 border-black bg-surface p-12 text-center space-y-3">
        <h2 className="font-serif italic text-2xl font-bold text-black">
          Investigator Ingesting Public Signals
        </h2>
        <p className="text-sm text-textMuted max-w-lg mx-auto">
          The multi-agent diagnostic engine is cross-examining KSNDMC rainfall radars, elevation slopes, and power telemetry.
        </p>
      </div>
    );
  }

  const hypothesisNames: Record<string, string> = {
    rain_overwhelm: 'Extreme Rainfall Runoff Exceeding Drainage Capacity',
    culvert_blockage: 'Primary Culvert Silt & Solid Waste Obstruction',
    power_led_stp: 'Substation Power Outage Halting Stormwater Pumps',
  };

  const getProvenanceBadge = (prov: string) => {
    switch (prov) {
      case 'real':
        return 'bg-black text-white border-black';
      case 'simulated':
        return 'bg-bone text-black border-black';
      case 'derived':
      default:
        return 'bg-white text-black border-borderDark';
    }
  };

  return (
    <div ref={containerRef} className="space-y-8">
      {/* Overview Header */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-borderSubtle pb-4">
          <div>
            <span className="text-[11px] font-mono uppercase text-textMuted tracking-wider block font-bold">
              Root Cause Diagnostics
            </span>
            <h2 className="text-2xl md:text-3xl font-serif font-bold italic text-black tracking-tight mt-1 max-w-5xl">
              Bayesian Hypothesis Ranking & Empirical Evidence
            </h2>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-mono border border-black bg-bone px-3 py-1 font-bold">
              STATUS: {dossier.conclusive ? 'CONCLUSIVE' : 'EVALUATING'}
            </span>
          </div>
        </div>
        <p className="text-sm text-textBody leading-relaxed max-w-4xl">
          Diagnostic conclusion: <strong>{dossier.stop_reason}</strong>. Public sensor readings and municipal feeds have been weighted into posterior probabilities.
        </p>
      </div>

      {/* Hypothesis Probability Bars */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-borderSubtle pb-3">
          <h3 className="font-serif font-bold italic text-lg text-black">
            Ranked Hypotheses
          </h3>
          <span className="text-xs font-mono text-textMuted">Posterior Confidence</span>
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
                    <span className={`font-serif ${isLeading ? 'font-bold italic text-black' : 'text-textBody'}`}>
                      {hypothesisNames[hypId] || hypId}
                    </span>
                  </div>
                  <span className="font-mono text-sm font-bold text-black">{percentage}%</span>
                </div>

                {/* GSAP Animated Probability Bar */}
                <div className="h-4 border border-black bg-bone w-full relative overflow-hidden">
                  <div
                    className={`prob-fill h-full ${isLeading ? 'bg-black' : 'bg-[#57606A]'}`}
                    style={{ width: `${percentage}%` }}
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
            Evidence Chain & Provenance Audit
          </h3>
          <span className="text-xs font-mono text-textMuted">{dossier.evidence.length} signals collected</span>
        </div>

        <div className="divide-y divide-borderSubtle">
          {dossier.evidence.map((ev) => (
            <div key={ev.id} className="py-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-black">{ev.tool}</span>
                  <span className="text-xs font-mono text-textMuted">({ev.source})</span>
                </div>
                <span className={`font-mono text-[10px] uppercase font-bold px-2 py-0.5 border ${getProvenanceBadge(ev.provenance)}`}>
                  {ev.provenance}
                </span>
              </div>
              <p className="text-sm text-textBody">{ev.summary}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
