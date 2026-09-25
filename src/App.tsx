import { useCallback, useEffect, useState } from "react";
import { checkHealth, createRun, getReport, getRun, listEvents, listSources } from "./api/client";
import "./App.css";
import { KpiTiles } from "./components/KpiTiles";
import { QueryForm } from "./components/QueryForm";
import { RunDetail } from "./components/RunDetail";
import { RunList } from "./components/RunList";
import type { Report, RunEvent, RunSummary, SourceDocument } from "./types";

const POLL_INTERVAL_MS = 3000;

function App() {
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [sources, setSources] = useState<SourceDocument[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    checkHealth().then(setBackendHealthy);
  }, []);

  const refreshSelectedRun = useCallback(async () => {
    if (selectedRunId === null) return;
    const [run, runEvents, runSources, runReport] = await Promise.all([
      getRun(selectedRunId),
      listEvents(selectedRunId),
      listSources(selectedRunId),
      getReport(selectedRunId),
    ]);
    if (run !== null) {
      setRuns((current) => current.map((item) => (item.id === run.id ? run : item)));
    }
    setEvents(runEvents);
    setSources(runSources);
    setReport(runReport);
  }, [selectedRunId]);

  useEffect(() => {
    // Fetching data for the newly selected run; setState happens async, not synchronously.
    // oxlint-disable-next-line react/set-state-in-effect
    refreshSelectedRun();
  }, [refreshSelectedRun]);

  useEffect(() => {
    const selectedRun = runs.find((run) => run.id === selectedRunId);
    if (!selectedRun || (selectedRun.status !== "queued" && selectedRun.status !== "running")) {
      return;
    }
    const timer = setInterval(refreshSelectedRun, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [runs, selectedRunId, refreshSelectedRun]);

  async function handleSubmit(question: string, depth: number, sourceTypes: string[]) {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const run = await createRun(question, depth, sourceTypes);
      setRuns((current) => [run, ...current]);
      setSelectedRunId(run.id);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Failed to start research");
    } finally {
      setSubmitting(false);
    }
  }

  const completedRuns = runs.filter((run) => run.status === "completed");
  const runningRuns = runs.filter((run) => run.status === "running" || run.status === "queued");
  const selectedRun = runs.find((run) => run.id === selectedRunId) ?? null;

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <h1>🧠 Research Mesh</h1>
        <p className="muted">Multi-agent research assistant with citation-backed reports.</p>
        {backendHealthy === false && (
          <p className="error-text">
            Cannot reach the Research Mesh API. Is the backend running?
          </p>
        )}
        <QueryForm onSubmit={handleSubmit} disabled={submitting} />
        {submitError && <p className="error-text">{submitError}</p>}

        <h2>Recent runs</h2>
        <RunList runs={runs} selectedRunId={selectedRunId} onSelect={setSelectedRunId} />
      </aside>

      <main className="main-content">
        <KpiTiles
          totalQueries={runs.length}
          reportsGenerated={completedRuns.length}
          sourcesUsed={sources.length}
          runsInProgress={runningRuns.length}
        />

        {selectedRun === null ? (
          <p className="muted">Submit a research question from the sidebar to get started.</p>
        ) : (
          <RunDetail
            run={selectedRun}
            events={events}
            sources={sources}
            report={report}
            onRefresh={refreshSelectedRun}
          />
        )}
      </main>
    </div>
  );
}

export default App;

