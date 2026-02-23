import SignalBadge from './SignalBadge';

interface ScoreGaugeProps {
  score: number;
  signalStrength: string;
  alignmentCount: number;
}

export default function ScoreGauge({ score, signalStrength, alignmentCount }: ScoreGaugeProps) {
  const clamped = Math.max(-1, Math.min(1, score));
  const markerPct = ((clamped + 1) / 2) * 100;

  const scoreColor = clamped > 0.2
    ? 'var(--signal-bullish)'
    : clamped < -0.2
      ? 'var(--signal-bearish)'
      : 'var(--signal-neutral)';

  return (
    <div className="text-center">
      {/* Large score */}
      <div
        className="font-mono text-4xl font-bold mb-2"
        style={{ color: scoreColor }}
      >
        {clamped >= 0 ? '+' : ''}{clamped.toFixed(2)}
      </div>

      {/* Signal badge */}
      <div className="mb-3">
        <SignalBadge strength={signalStrength} />
      </div>

      {/* Gradient bar with marker */}
      <div className="relative h-2 rounded-full overflow-hidden mb-2"
        style={{
          background: 'linear-gradient(to right, var(--signal-bearish), var(--signal-neutral), var(--signal-bullish))',
        }}
      >
        <div
          className="absolute top-[-2px] w-3 h-3 rounded-full border-2"
          style={{
            left: `calc(${markerPct}% - 6px)`,
            backgroundColor: 'var(--bg-void)',
            borderColor: scoreColor,
          }}
        />
      </div>

      {/* Alignment count */}
      <p
        className="text-xs font-mono"
        style={{ color: 'var(--text-muted)' }}
      >
        {alignmentCount}/7 layers aligned
      </p>
    </div>
  );
}
