import { useState, useEffect, useCallback } from 'react';
import { HeaderNav } from './components/nav/HeaderNav';
import { CitizenReports } from './components/reports/CitizenReports';
import { CityFloodMap } from './components/map/CityFloodMap';
import { CauseAnalysis } from './components/cause/CauseAnalysis';
import { DispatchConsole } from './components/dispatch/DispatchConsole';
import { IntakeModal } from './components/intake/IntakeModal';
import {
  fetchIncidents,
  fetchIncidentDetail,
  submitDecision,
  verifyIncident,
  loadScenario,
  resetSystem,
} from './api/client';
import { Incident, Ticket, Dossier, ActionProposal } from './types/api';

export default function App() {
  const [activeStage, setActiveStage] = useState<1 | 2 | 3 | 4>(1);
  const [allIncidents, setAllIncidents] = useState<Incident[]>([]);
  const [incident, setIncident] = useState<Incident | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [actions, setActions] = useState<ActionProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isIntakeOpen, setIsIntakeOpen] = useState(false);

  const loadDataForIncident = useCallback(async (targetId?: string) => {
    try {
      setLoading(true);
      const incList = await fetchIncidents();
      setAllIncidents(incList || []);

      if (incList && incList.length > 0) {
        const activeInc = targetId
          ? incList.find((i) => i.id === targetId) || incList[0]
          : incList[0];
        setIncident(activeInc);

        const detail = await fetchIncidentDetail(activeInc.id);
        setDossier(detail.dossier ?? null);
        setActions(detail.actions ?? []);
        setTickets(detail.tickets ?? []);
      } else {
        setIncident(null);
        setTickets([]);
        setDossier(null);
        setActions([]);
      }
    } catch (err) {
      console.warn('Backend query notice:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDataForIncident();
  }, [loadDataForIncident]);

  const handleSelectIncident = async (id: string) => {
    await loadDataForIncident(id);
  };

  const handleScenarioLoad = async () => {
    try {
      setLoading(true);
      const res = await loadScenario('bellandur_flood');
      const incId = (res as { incident_id?: string }).incident_id;
      await loadDataForIncident(incId);
    } catch (e) {
      console.error('Failed to load scenario:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      setLoading(true);
      await resetSystem();
      setIncident(null);
      setAllIncidents([]);
      setTickets([]);
      setDossier(null);
      setActions([]);
      setActiveStage(1);
    } catch (e) {
      console.error('Failed to reset system:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorize = async (approvedIds?: string[], officer?: string) => {
    if (!incident) return;
    setIsSubmitting(true);
    try {
      await submitDecision(incident.id, {
        incident_id: incident.id,
        approved: true,
        approved_action_ids: approvedIds || actions.map((a, i) => a.id || `act-${i + 1}`),
        officer: officer || 'Chief Disaster Coordinator, BBMP Central Cell',
      });
      setIncident({ ...incident, status: 'dispatched' });
      await loadDataForIncident(incident.id);
    } catch (e) {
      console.warn('Decision dispatch result:', e);
      setIncident({ ...incident, status: 'dispatched' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerify = async () => {
    if (!incident) return;
    setIsSubmitting(true);
    try {
      await verifyIncident(incident.id, 45);
      setIncident({ ...incident, status: 'closed' });
      await loadDataForIncident(incident.id);
    } catch (e) {
      console.warn('Verification result:', e);
      setIncident({ ...incident, status: 'closed' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col font-sans bg-canvas text-textBody">
      <HeaderNav
        activeStage={activeStage}
        onSelectStage={setActiveStage}
        incident={incident}
        allIncidents={allIncidents}
        onSelectIncident={handleSelectIncident}
        onOpenIntake={() => setIsIntakeOpen(true)}
        onLoadScenario={handleScenarioLoad}
        onRefresh={() => loadDataForIncident(incident?.id)}
        onReset={handleReset}
        isLoading={loading}
      />

      <main className="flex-1 max-w-6xl mx-auto w-full px-4 md:px-8 py-6 md:py-10 overflow-x-hidden">
        {loading ? (
          <div className="border-2 border-black bg-surface p-12 text-center font-mono text-sm space-y-2">
            <div className="animate-pulse font-bold text-black">Querying CrossWire Incident Core...</div>
            <div className="text-xs text-textMuted">Reading active municipal repository and telemetries</div>
          </div>
        ) : (
          <>
            {activeStage === 1 && (
              <CitizenReports
                tickets={tickets}
                incident={incident}
                onOpenIntake={() => setIsIntakeOpen(true)}
                onLoadScenario={handleScenarioLoad}
              />
            )}
            {activeStage === 2 && (
              <CityFloodMap incident={incident} tickets={tickets} />
            )}
            {activeStage === 3 && (
              <CauseAnalysis dossier={dossier} incident={incident} />
            )}
            {activeStage === 4 && (
              <DispatchConsole
                incident={incident}
                actions={actions}
                onAuthorize={handleAuthorize}
                onVerify={handleVerify}
                isSubmitting={isSubmitting}
              />
            )}
          </>
        )}
      </main>

      <IntakeModal
        isOpen={isIntakeOpen}
        onClose={() => setIsIntakeOpen(false)}
        onSuccess={async () => {
          await loadDataForIncident();
          setActiveStage(1);
        }}
      />

      <footer className="border-t-2 border-black bg-white py-6">
        <div className="max-w-6xl mx-auto px-4 md:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-textMuted">
          <div>CrossWire Incident Command Console · Bengaluru Municipal Response</div>
          <div className="flex items-center gap-4 font-semibold text-black">
            <span>BBMP</span>
            <span>·</span>
            <span>BWSSB</span>
            <span>·</span>
            <span>BTP</span>
            <span>·</span>
            <span>KSNDMC</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
