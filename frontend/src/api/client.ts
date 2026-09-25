import type { Report, RunEvent, RunSummary, SourceDocument } from "../types";

const DEFAULT_BASE_URL = "http://localhost:8000";

export class ApiError extends Error {}

function baseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;
}

async function request<T>(path: string, init?: RequestInit): Promise<T | null> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (error) {
    throw new ApiError(`Network error calling ${path}: ${String(error)}`);
  }

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(`Request to ${path} failed (${response.status}): ${body}`);
  }
  return (await response.json()) as T;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl()}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function createRun(
  question: string,
  depth: number,
  sourceTypes: string[],
): Promise<RunSummary> {
  const run = await request<RunSummary>("/runs", {
    method: "POST",
    body: JSON.stringify({ question, depth, source_types: sourceTypes }),
  });
  if (run === null) {
    throw new ApiError("Create run returned no data");
  }
  return run;
}

export async function getRun(runId: string): Promise<RunSummary | null> {
  return request<RunSummary>(`/runs/${runId}`);
}

export async function listEvents(runId: string): Promise<RunEvent[]> {
  return (await request<RunEvent[]>(`/runs/${runId}/events`)) ?? [];
}

export async function listSources(runId: string): Promise<SourceDocument[]> {
  return (await request<SourceDocument[]>(`/runs/${runId}/sources`)) ?? [];
}

export async function getReport(runId: string): Promise<Report | null> {
  return request<Report>(`/runs/${runId}/report`);
}
