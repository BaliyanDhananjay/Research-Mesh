import type { Report, RunEvent, RunSummary, SourceDocument } from "../types";

const STATUS_ICON: Record<string, string> = {
  queued: "🕓",
  running: "⚙️",
  completed: "✅",
  failed: "❌",
  cancelled: "🚫",
};

interface RunDetailProps {
  run: RunSummary;
  events: RunEvent[];
  sources: SourceDocument[];
  report: Report | null;
  onRefresh: () => void;
}

export function RunDetail({ run, events, sources, report, onRefresh }: RunDetailProps) {
  const sortedSources = [...sources].sort((a, b) => b.quality_score - a.quality_score);
  const isInProgress = run.status === "queued" || run.status === "running";

  return (
    <div className="run-detail">
      <h2>{run.request.question}</h2>
      <p className="run-meta">
        Run {run.id.slice(0, 8)} · {STATUS_ICON[run.status] ?? "•"}{" "}
        {run.status.charAt(0).toUpperCase() + run.status.slice(1)}
      </p>
      {run.error && <p className="error-text">Run failed: {run.error}</p>}
      {isInProgress && (
        <button className="secondary-button" onClick={onRefresh}>
          Refresh status
        </button>
      )}

      <div className="run-columns">
        <section>
          <h3>Research process</h3>
          {events.length === 0 ? (
            <p className="muted">No activity recorded yet.</p>
          ) : (
            <ul className="event-list">
              {events.map((event) => (
                <li key={event.id}>
                  <strong>{event.event_type}</strong> — {event.message}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h3>Sources</h3>
          {sortedSources.length === 0 ? (
            <p className="muted">No sources indexed yet.</p>
          ) : (
            <ul className="source-list">
              {sortedSources.map((source) => (
                <li key={source.id}>
                  <a href={source.url} target="_blank" rel="noreferrer">
                    {source.title || source.domain}
                  </a>{" "}
                  · score {source.quality_score.toFixed(2)}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section>
        <h3>Report</h3>
        {report === null ? (
          <p className="muted">Report not available yet.</p>
        ) : (
          <div className="report-card">
            <h4>{report.title}</h4>
            <p>{report.summary}</p>
            <p className="muted">Citations: {report.citations.length}</p>
            <ul>
              {report.claims.map((claim) => (
                <li key={claim.id}>
                  {claim.text} <span className="muted">(confidence {claim.confidence.toFixed(2)})</span>
                </li>
              ))}
            </ul>
            {report.limitations.length > 0 && (
              <>
                <h5>Limitations</h5>
                <ul>
                  {report.limitations.map((limitation) => (
                    <li key={limitation}>{limitation}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
