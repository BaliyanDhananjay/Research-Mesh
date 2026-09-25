interface KpiTilesProps {
  totalQueries: number;
  reportsGenerated: number;
  sourcesUsed: number;
  runsInProgress: number;
}

export function KpiTiles({
  totalQueries,
  reportsGenerated,
  sourcesUsed,
  runsInProgress,
}: KpiTilesProps) {
  const tiles = [
    { label: "Total queries", value: totalQueries },
    { label: "Reports generated", value: reportsGenerated },
    { label: "Sources used", value: sourcesUsed },
    { label: "Runs in progress", value: runsInProgress },
  ];

  return (
    <div className="kpi-row" data-testid="kpi-tiles">
      {tiles.map((tile) => (
        <div className="kpi-tile" key={tile.label}>
          <span className="kpi-value">{tile.value}</span>
          <span className="kpi-label">{tile.label}</span>
        </div>
      ))}
    </div>
  );
}
