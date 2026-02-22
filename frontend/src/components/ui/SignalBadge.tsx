interface SignalBadgeProps {
  strength: string;
}

export default function SignalBadge({ strength }: SignalBadgeProps) {
  const upper = strength.toUpperCase();
  let bg: string;
  let text: string;

  if (upper.includes('STRONG BUY') || upper.includes('BUY')) {
    bg = 'var(--signal-bullish)';
    text = 'var(--bg-void)';
  } else if (upper.includes('STRONG SELL') || upper.includes('SELL')) {
    bg = 'var(--signal-bearish)';
    text = 'var(--bg-void)';
  } else {
    bg = 'var(--signal-neutral)';
    text = 'var(--bg-void)';
  }

  return (
    <span
      className="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider"
      style={{ backgroundColor: bg, color: text }}
    >
      {strength}
    </span>
  );
}
