import { usePolitical } from '../../hooks/usePolitical';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';

function directionArrow(dir: string | null): string {
  if (!dir) return '';
  const lower = dir.toLowerCase();
  if (lower === 'bullish') return '▲';
  if (lower === 'bearish') return '▼';
  return '—';
}

function directionColor(dir: string | null): string {
  if (!dir) return 'var(--text-muted)';
  const lower = dir.toLowerCase();
  if (lower === 'bullish') return 'var(--signal-bullish)';
  if (lower === 'bearish') return 'var(--signal-bearish)';
  return 'var(--signal-neutral)';
}

export default function PoliticalCard() {
  const { data, isLoading } = usePolitical();

  if (isLoading) {
    return (
      <Card title="Political" layerColor="var(--layer-political)">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </Card>
    );
  }

  const signal = data?.signal;
  if (!signal) {
    return (
      <Card title="Political" layerColor="var(--layer-political)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No political signal data</p>
      </Card>
    );
  }

  const score = parseScore(signal.political_score);

  return (
    <Card title="Political" layerColor="var(--layer-political)">
      <LayerBar label="Score" score={score} color="var(--layer-political)" />

      <div className="mt-3 space-y-2">
        {/* Next major event */}
        {signal.next_event_type && (
          <div className="flex justify-between items-center">
            <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Next Event</span>
            <div className="text-right">
              <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>
                {signal.next_event_type}
              </span>
              {signal.hours_to_next_major_event != null && (
                <span className="font-mono text-[10px] ml-1" style={{ color: 'var(--accent-gold)' }}>
                  {signal.hours_to_next_major_event}h
                </span>
              )}
            </div>
          </div>
        )}

        {/* News volume */}
        <div className="flex justify-between items-center">
          <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>News (24h)</span>
          <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>
            {signal.news_volume_24h ?? 0} articles
          </span>
        </div>

        {/* Dominant narrative */}
        {signal.dominant_narrative && (
          <div>
            <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Narrative</span>
            <div className="flex items-center gap-1 mt-0.5">
              <span className="text-xs" style={{ color: 'var(--text-primary)' }}>
                {signal.dominant_narrative}
              </span>
              <span style={{ color: directionColor(signal.narrative_direction) }}>
                {directionArrow(signal.narrative_direction)}
              </span>
            </div>
          </div>
        )}

        {/* Narrative strength bar */}
        {signal.narrative_strength && (
          <div>
            <div className="flex justify-between mb-0.5">
              <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Strength</span>
              <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
                {parseScore(signal.narrative_strength).toFixed(2)}
              </span>
            </div>
            <div className="h-1 rounded-full" style={{ backgroundColor: 'var(--bg-elevated)' }}>
              <div
                className="h-full rounded-full"
                style={{
                  width: `${Math.min(100, parseScore(signal.narrative_strength) * 100)}%`,
                  backgroundColor: 'var(--layer-political)',
                }}
              />
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
