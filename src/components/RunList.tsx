import type { RunSummary } from "../types";

const STATUS_ICON: Record<string, string> = {
  queued: "🕓",
  running: "⚙️",
  completed: "✅",
  failed: "❌",
  cancelled: "🚫",
};

interface RunListProps {
  runs: RunSummary[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}

export function RunList({ runs, selectedRunId, onSelect }: RunListProps) {
  if (runs.length === 0) {
    return <p className="muted">No runs yet this session.</p>;
  }

  return (
    <ul className="run-list">
      {runs.map((run) => (
        <li key={run.id}>
          <button
            className={run.id === selectedRunId ? "run-item run-item-active" : "run-item"}
            onClick={() => onSelect(run.id)}
          >
            <span>{STATUS_ICON[run.status] ?? "•"}</span>
            <span className="run-item-question">{run.request.question}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
