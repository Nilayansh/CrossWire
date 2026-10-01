export type IncidentStatus =
  | 'open'
  | 'investigating'
  | 'awaiting_approval'
  | 'dispatched'
  | 'resolving'
  | 'closed'
  | 'escalated';

export interface Ticket {
  id: string;
  ts: string;
  channel: 'telegram' | 'web' | 'synthetic';
  lang: string;
  text_original: string;
  text_en: string;
  category: string;
  severity: number;
  lat: number;
  lon: number;
  geo_confidence: number;
  h3_r8: string;
  photo_depth?: 'ankle' | 'knee' | 'waist' | 'vehicle' | null;
  reporter_chat_id?: string | null;
  is_synthetic?: boolean;
  image_data?: string | null;
}

export interface Incident {
  id: string;
  opened_at: string;
  status: IncidentStatus;
  ticket_ids: string[];
  centroid: [number, number];
  cells: string[];
  category_mix: Record<string, number>;
  reinvestigate?: boolean;
}

export type ProvenanceType = 'real' | 'simulated' | 'derived';

export interface Evidence {
  id: string;
  tool: string;
  ts: string;
  summary: string;
  keys: string[];
  source: string;
  provenance: ProvenanceType;
  raw?: Record<string, unknown>;
}

export interface Dossier {
  incident_id: string;
  ranked: [string, number][]; // [hypothesis_id, probability]
  evidence: Evidence[];
  conclusive: boolean;
  stop_reason: string;
  trace: Record<string, unknown>[];
}

export interface ActionProposal {
  id?: string;
  dept: 'stormwater' | 'power_utility' | 'sewerage' | 'traffic_police' | 'solid_waste' | 'water_board';
  action: string;
  target_latlon?: [number, number] | null;
  priority: 'P1' | 'P2' | 'P3';
  rationale: string;
  evidence_ids: string[];
  confidence: number;
}

export interface IncidentDetailResponse {
  incident: Incident;
  status: IncidentStatus;
  dossier?: Dossier | null;
  actions: ActionProposal[];
  tickets?: Ticket[];
}

export interface DecisionPayload {
  incident_id: string;
  approved: boolean;
  modified_actions?: ActionProposal[] | null;
  feedback?: string | null;
  approved_action_ids?: string[];
  officer?: string;
}

export interface VerifyResponse {
  incident_id: string;
  status: IncidentStatus;
  verify_result: string;
  fast_forward_min: number;
}
