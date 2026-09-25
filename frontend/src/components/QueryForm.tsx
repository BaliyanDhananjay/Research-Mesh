import { useState } from "react";

interface QueryFormProps {
  onSubmit: (question: string, depth: number, sourceTypes: string[]) => void;
  disabled: boolean;
}

const SOURCE_OPTIONS = ["academic", "official", "news", "general"];

export function QueryForm({ onSubmit, disabled }: QueryFormProps) {
  const [question, setQuestion] = useState("");
  const [depth, setDepth] = useState(2);
  const [sourceTypes, setSourceTypes] = useState<string[]>(["academic", "official"]);
  const [validationError, setValidationError] = useState<string | null>(null);

  function toggleSourceType(type: string) {
    setSourceTypes((current) =>
      current.includes(type) ? current.filter((item) => item !== type) : [...current, type],
    );
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (question.trim().length < 5) {
      setValidationError("Please enter a more complete research question.");
      return;
    }
    setValidationError(null);
    onSubmit(question.trim(), depth, sourceTypes);
  }

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <h2>New research query</h2>
      <label htmlFor="question">Research question</label>
      <textarea
        id="question"
        placeholder="What causes coral bleaching?"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        rows={3}
      />

      <label htmlFor="depth">Research depth: {depth}</label>
      <input
        id="depth"
        type="range"
        min={1}
        max={5}
        value={depth}
        onChange={(event) => setDepth(Number(event.target.value))}
      />

      <span className="label">Source types</span>
      <div className="chip-row">
        {SOURCE_OPTIONS.map((type) => (
          <button
            type="button"
            key={type}
            className={sourceTypes.includes(type) ? "chip chip-active" : "chip"}
            onClick={() => toggleSourceType(type)}
          >
            {type}
          </button>
        ))}
      </div>

      {validationError && <p className="error-text">{validationError}</p>}

      <button type="submit" className="primary-button" disabled={disabled}>
        Start research
      </button>
    </form>
  );
}
