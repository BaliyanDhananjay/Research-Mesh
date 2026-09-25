import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, checkHealth, createRun, getReport, getRun, listSources } from "./client";

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
      text: async () => JSON.stringify(body),
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("creates a run and returns the parsed summary", async () => {
    mockFetchOnce(202, {
      id: "run-1",
      status: "queued",
      request: { question: "What causes coral bleaching?", depth: 2, source_types: ["official"] },
      created_at: "2026-09-25T00:00:00Z",
      updated_at: "2026-09-25T00:00:00Z",
      error: null,
    });

    const run = await createRun("What causes coral bleaching?", 2, ["official"]);

    expect(run.id).toBe("run-1");
    expect(run.status).toBe("queued");
  });

  it("throws ApiError when the backend returns a failure status", async () => {
    mockFetchOnce(500, { detail: "boom" });

    await expect(createRun("What causes coral bleaching?", 2, ["official"])).rejects.toThrow(
      ApiError,
    );
  });

  it("returns null for a 404 run lookup", async () => {
    mockFetchOnce(404, { detail: "Run not found" });

    const run = await getRun("missing");

    expect(run).toBeNull();
  });

  it("returns an empty list when sources are not found", async () => {
    mockFetchOnce(404, { detail: "Run not found" });

    const sources = await listSources("missing");

    expect(sources).toEqual([]);
  });

  it("returns null for a report that is not ready yet", async () => {
    mockFetchOnce(404, { detail: "Report not available yet" });

    const report = await getReport("run-1");

    expect(report).toBeNull();
  });

  it("reports unhealthy when fetch throws", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("connection refused")),
    );

    expect(await checkHealth()).toBe(false);
  });
});
