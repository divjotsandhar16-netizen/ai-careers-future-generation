type ScoreRingProps = {
  score: number;
  label?: string;
};

export function ScoreRing({ score, label = "Readiness" }: ScoreRingProps) {
  const safeScore = Math.max(0, Math.min(score, 100));
  return (
    <div className="score-ring" style={{ "--score": `${safeScore * 3.6}deg` } as React.CSSProperties}>
      <div>
        <strong>{Math.round(safeScore)}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}
