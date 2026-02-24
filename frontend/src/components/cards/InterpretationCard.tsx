import { useInterpretation } from '../../hooks/useInterpretation';
import Card from '../ui/Card';
import Skeleton from '../ui/Skeleton';

const LAYER_LABELS: Record<string, string> = {
  ta: 'TA',
  sentiment: 'Sentiment',
  political: 'Political',
  macro: 'Macro',
  celestial: 'Celestial',
  numerology: 'Numerology',
  onchain: 'On-Chain',
};

const LAYER_COLORS: Record<string, string> = {
  ta: 'var(--layer-ta)',
  sentiment: 'var(--layer-sentiment)',
  political: 'var(--layer-political)',
  macro: 'var(--layer-macro)',
  celestial: 'var(--layer-celestial)',
  numerology: 'var(--layer-numerology)',
  onchain: 'var(--layer-onchain)',
};

function biasColor(bias: string): string {
  if (bias.includes('bullish')) return 'var(--signal-bullish)';
  if (bias.includes('bearish')) return 'var(--signal-bearish)';
  return 'var(--signal-neutral)';
}

function biasLabel(bias: string): string {
  return bias.replace(/_/g, ' ');
}

function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  return `${hours}h ago`;
}

export default function InterpretationCard() {
  const { data, isLoading } = useInterpretation();

  if (isLoading) {
    return (
      <Card title="AI Analysis">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6 mt-2" />
        <Skeleton className="h-4 w-4/6 mt-2" />
        <Skeleton className="h-3 w-3/4 mt-3" />
        <Skeleton className="h-3 w-2/3 mt-2" />
      </Card>
    );
  }

  if (!data || !data.summary) {
    return (
      <Card title="AI Analysis">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          No interpretation available
        </p>
      </Card>
    );
  }

  const layerEntries = Object.entries(data.layers || {});

  return (
    <Card title="AI Analysis">
      {/* Summary */}
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
        {data.summary}
      </p>

      {/* Layer insights */}
      {layerEntries.length > 0 && (
        <div className="mt-3 space-y-1.5">
          {layerEntries.map(([key, insight]) => (
            <div key={key} className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              <span className="font-semibold" style={{ color: LAYER_COLORS[key] || 'var(--text-primary)' }}>
                {LAYER_LABELS[key] || key}:
              </span>{' '}
              {insight}
            </div>
          ))}
        </div>
      )}

      {/* Watch */}
      {data.watch && (
        <div
          className="mt-3 text-xs font-medium px-2 py-1.5 rounded"
          style={{
            color: 'var(--accent-gold)',
            backgroundColor: 'rgba(212, 168, 70, 0.08)',
            borderLeft: '2px solid var(--accent-gold)',
          }}
        >
          {data.watch}
        </div>
      )}

      {/* Footer: bias + timestamp */}
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span
            className="w-2 h-2 rounded-full inline-block"
            style={{ backgroundColor: biasColor(data.bias) }}
          />
          <span className="text-[11px] font-mono capitalize" style={{ color: biasColor(data.bias) }}>
            {biasLabel(data.bias)}
          </span>
        </div>
        <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
          {data.cached && 'cached · '}
          {data.generated_at ? timeAgo(data.generated_at) : ''}
        </span>
      </div>
    </Card>
  );
}
