import { FC, useState } from 'react';
import { ActionProposal, Incident } from '../../types/api';
import { CheckCircle2, FastForward, Send } from 'lucide-react';

interface DispatchConsoleProps {
  incident: Incident | null;
  actions: ActionProposal[];
  onAuthorize: () => Promise<void>;
  onVerify: () => Promise<void>;
  isSubmitting: boolean;
}

export const DispatchConsole: FC<DispatchConsoleProps> = ({
  incident,
  actions,
  onAuthorize,
  onVerify,
  isSubmitting,
}) => {
  const [authorized, setAuthorized] = useState(incident?.status === 'dispatched');
  const [verifiedResult, setVerifiedResult] = useState<string | null>(null);

  const handleAuthorizeClick = async () => {
    await onAuthorize();
    setAuthorized(true);
  };

  const handleVerifyClick = async () => {
    await onVerify();
    setVerifiedResult('Dewatering validated: Water level reduced to baseline (3cm). Traffic flow restored on Outer Ring Road.');
  };

  const departmentTitles: Record<string, string> = {
    stormwater: 'BBMP Stormwater Drain Division (SWD)',
    traffic_police: 'Bengaluru City Traffic Police (BTP)',
    sewerage: 'BWSSB Wastewater & Dewatering Unit',
    power_utility: 'BESCOM Electrical Substation Division',
    solid_waste: 'BBMP Solid Waste Management (SWM)',
    water_board: 'BWSSB Water Supply',
  };

  return (
    <div className="space-y-8">
      {/* Console Header */}
      <div className="border-2 border-black bg-surface p-6 md:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-borderSubtle pb-4">
          <div>
            <span className="text-[11px] font-mono uppercase text-textMuted tracking-wider block font-bold">
              HITL Coordination Desk
            </span>
            <h2 className="text-2xl md:text-3xl font-serif font-bold italic text-black tracking-tight mt-1 max-w-5xl">
              Authorize Inter-Agency Municipal Directives
            </h2>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-mono border-2 border-black bg-black text-white px-3 py-1 font-bold">
              {actions.length} DIRECTIVES QUEUED
            </span>
          </div>
        </div>
        <p className="text-sm text-textBody leading-relaxed max-w-4xl">
          Review targeted emergency orders synthesized by the planner. Authorizing issues real-time work orders across BBMP, BWSSB, and Bengaluru Traffic Police.
        </p>
      </div>

      {/* Action Orders List */}
      <div className="space-y-4">
        {actions.map((act, index) => (
          <div key={index} className="border-2 border-black bg-surface p-6 space-y-3">
            <div className="flex items-center justify-between border-b border-borderSubtle pb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold border border-black bg-bone px-2 py-0.5">
                  {act.priority}
                </span>
                <span className="font-serif font-bold italic text-base text-black">
                  {departmentTitles[act.dept] || act.dept}
                </span>
              </div>
              <span className="font-mono text-xs text-textMuted">Confidence: {Math.round(act.confidence * 100)}%</span>
            </div>

            <p className="text-sm font-medium text-black">{act.action}</p>
            <p className="text-xs text-textMuted leading-relaxed">{act.rationale}</p>
          </div>
        ))}
      </div>

      {/* Dispatch Authorization Bar */}
      <div className="border-2 border-black bg-bone p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <h4 className="font-serif font-bold italic text-lg text-black">
            Human-In-The-Loop Approval Desk
          </h4>
          <p className="text-xs text-textMuted">
            Requires municipal coordinator sign-off before dispatching emergency teams.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          {!authorized ? (
            <button
              onClick={handleAuthorizeClick}
              disabled={isSubmitting}
              className="flex-1 md:flex-none border-2 border-black bg-black text-white px-6 py-2.5 font-mono text-xs font-bold uppercase tracking-wider hover:bg-white hover:text-black transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <Send className="w-4 h-4" />
              {isSubmitting ? 'Issuing Orders...' : 'Authorize & Issue Departmental Orders'}
            </button>
          ) : (
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold text-black border border-black bg-white px-3 py-2 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-black" />
                Orders Dispatched
              </span>
              <button
                onClick={handleVerifyClick}
                disabled={isSubmitting}
                className="border-2 border-black bg-bone hover:bg-black hover:text-white transition-colors px-4 py-2 font-mono text-xs font-bold flex items-center gap-1.5 cursor-pointer"
              >
                <FastForward className="w-4 h-4" />
                Fast-Forward 45m & Verify
              </button>
            </div>
          )}
        </div>
      </div>

      {verifiedResult && (
        <div className="border-2 border-black bg-white p-6 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-black">
            <CheckCircle2 className="w-4 h-4 text-black" />
            <span>Verification Assessment Completed</span>
          </div>
          <p className="text-sm text-textBody">{verifiedResult}</p>
        </div>
      )}
    </div>
  );
};
