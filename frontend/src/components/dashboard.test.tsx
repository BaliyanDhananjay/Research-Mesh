import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { KpiTiles } from "./KpiTiles";
import { QueryForm } from "./QueryForm";

describe("QueryForm", () => {
  it("blocks submission for a too-short question", async () => {
    const onSubmit = vi.fn();
    render(<QueryForm onSubmit={onSubmit} disabled={false} />);

    await userEvent.type(screen.getByLabelText(/research question/i), "hi");
    await userEvent.click(screen.getByRole("button", { name: /start research/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/more complete research question/i)).toBeInTheDocument();
  });

  it("submits with the entered question and selected sources", async () => {
    const onSubmit = vi.fn();
    render(<QueryForm onSubmit={onSubmit} disabled={false} />);

    await userEvent.type(
      screen.getByLabelText(/research question/i),
      "What causes coral bleaching?",
    );
    await userEvent.click(screen.getByRole("button", { name: /start research/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      "What causes coral bleaching?",
      2,
      expect.arrayContaining(["academic", "official"]),
    );
  });
});

describe("KpiTiles", () => {
  it("renders every provided metric", () => {
    render(
      <KpiTiles totalQueries={3} reportsGenerated={2} sourcesUsed={5} runsInProgress={1} />,
    );

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });
});
