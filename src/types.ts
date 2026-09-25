export type RunStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export interface ResearchRequestPayload {
  question: string;
  depth: number;
  source_types: string[];
}

export interface RunSummary {
  id: string;
  status: RunStatus;
  request: ResearchRequestPayload;
  created_at: string;
  updated_at: string;
  error: string | null;
}

export interface RunEvent {
  id: string;
  run_id: string;
  event_type: string;
  message: string;
  created_at: string;
}

export interface SourceDocument {
  id: string;
  run_id: string;
  url: string;
  title: string;
  source_type: string;
  domain: string;
  quality_score: number;
  content_hash: string | null;
}

export interface Claim {
  id: string;
  text: string;
  evidence_ids: string[];
  confidence: number;
}

export interface Citation {
  claim_id: string;
  source_id: string;
  label: string;
}

export interface Report {
  id: string;
  run_id: string;
  title: string;
  summary: string;
  claims: Claim[];
  citations: Citation[];
  limitations: string[];
}
