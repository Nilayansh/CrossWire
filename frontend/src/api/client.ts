import {
  Incident,
  IncidentDetailResponse,
  DecisionPayload,
  VerifyResponse,
} from '../types/api';

const BASE_URL = '';

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch(`${BASE_URL}/incidents`);
  if (!res.ok) {
    throw new Error(`Failed to fetch incidents: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchIncidentDetail(id: string): Promise<IncidentDetailResponse> {
  const res = await fetch(`${BASE_URL}/incidents/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch incident ${id}: ${res.statusText}`);
  }
  return res.json();
}

export async function submitDecision(
  id: string,
  payload: DecisionPayload
): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE_URL}/incidents/${encodeURIComponent(id)}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit decision: ${res.statusText}`);
  }
  return res.json();
}

export async function ingestTicket(ticket: Record<string, unknown>): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE_URL}/tickets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticket),
  });
  if (!res.ok) {
    throw new Error(`Failed to ingest ticket: ${res.statusText}`);
  }
  return res.json();
}

export async function loadScenario(name = 'bellandur_flood'): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE_URL}/scenarios/load?name=${encodeURIComponent(name)}`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error(`Failed to load scenario: ${res.statusText}`);
  }
  return res.json();
}

export async function verifyIncident(
  id: string,
  fastForwardMin = 45
): Promise<VerifyResponse> {
  const res = await fetch(
    `${BASE_URL}/incidents/${encodeURIComponent(id)}/verify?fast_forward_min=${fastForwardMin}`,
    {
      method: 'POST',
    }
  );
  if (!res.ok) {
    throw new Error(`Failed to verify incident: ${res.statusText}`);
  }
  return res.json();
}

export async function processAudio(base64Data: string): Promise<{
  transcript: string;
  lang: string;
  text_en: string;
  category: string;
  severity: number;
}> {
  const res = await fetch(`${BASE_URL}/intake/audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ base64_data: base64Data }),
  });
  if (!res.ok) {
    throw new Error(`Audio processing error: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchTrafficFlow(lat = 12.926, lon = 77.683): Promise<{
  current_speed: number;
  free_flow_speed: number;
  speed_ratio: number;
  congestion: string;
  summary: string;
}> {
  const res = await fetch(`${BASE_URL}/traffic/flow?lat=${lat}&lon=${lon}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch traffic flow: ${res.statusText}`);
  }
  return res.json();
}

export async function geocodeLocation(query: string): Promise<{
  lat: number;
  lon: number;
  confidence: number;
  h3_r8: string;
}> {
  const res = await fetch(`${BASE_URL}/intake/geocode?query=${encodeURIComponent(query)}`);
  if (!res.ok) {
    throw new Error(`Failed to geocode location: ${res.statusText}`);
  }
  return res.json();
}
