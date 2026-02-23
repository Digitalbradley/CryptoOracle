import Tooltip from './Tooltip';

interface LayerBarProps {
  label: string;
  tooltip?: string;
  score: number;
  color: string;
  weight?: number;
}

export default function LayerBar({ label, tooltip, score, color, weight }: LayerBarProps) {
  const clampedScore = Math.max(-1, Math.min(1, score));
  const pct = Math.abs(clampedScore) * 50;
  const isPositive = clampedScore >= 0;

  return (
    <div className="flex items-center gap-2 py-1">
      {/* Label */}
      <span
        className="text-xs w-20 shrink-0"
        style={{ color: 'var(--text-secondary)' }}
      >
        {tooltip ? <Tooltip text={tooltip}>{label}</Tooltip> : label}
      </span>

      {/* Bar container */}
      <div
        className="flex-1 h-2 rounded-full relative overflow-hidden"
        style={{ backgroundColor: 'var(--bg-elevated)' }}
      >
        {/* Center line */}
        <div
          className="absolute top-0 bottom-0 w-px"
          style={{ left: '50%', backgroundColor: 'var(--border-subtle)' }}
        />
        {/* Fill bar */}
        <div
          className="absolute top-0 bottom-0 rounded-full"
          style={{
            backgroundColor: color,
            width: `${pct}%`,
            left: isPositive ? '50%' : `${50 - pct}%`,
            opacity: 0.85,
          }}
        />
      </div>

      {/* Score value */}
      <span
        className="font-mono text-xs w-12 text-right shrink-0"
        style={{
          color: clampedScore > 0
            ? 'var(--signal-bullish)'
            : clampedScore < 0
              ? 'var(--signal-bearish)'
              : 'var(--signal-neutral)',
        }}
      >
        {clampedScore >= 0 ? '+' : ''}{clampedScore.toFixed(2)}
      </span>

      {/* Weight */}
      <span
        className="font-mono text-[10px] w-8 text-right shrink-0"
        style={{ color: 'var(--text-muted)' }}
      >
        {weight != null ? (
          <Tooltip text="This layer's weight in the composite score">
            {(weight * 100).toFixed(0)}%
          </Tooltip>
        ) : ''}
      </span>
    </div>
  );
}
