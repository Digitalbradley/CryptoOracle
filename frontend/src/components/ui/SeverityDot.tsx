interface SeverityDotProps {
  severity: string;
}

export default function SeverityDot({ severity }: SeverityDotProps) {
  const lower = severity.toLowerCase();
  let color: string;

  if (lower === 'critical') {
    color = 'var(--severity-critical)';
  } else if (lower === 'warning') {
    color = 'var(--severity-warning)';
  } else {
    color = 'var(--severity-info)';
  }

  return (
    <span
      className="inline-block w-2 h-2 rounded-full shrink-0"
      style={{ backgroundColor: color }}
    />
  );
}
