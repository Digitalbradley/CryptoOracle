import { useState } from 'react';
import { useInterpretation } from '../../hooks/useInterpretation';
import Card from '../ui/Card';
import Skeleton from '../ui/Skeleton';
import ChatPanel from './ChatPanel';

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
  const { data, isLoading, isFetching, refresh } = useInterpretation();
  const [chatOpen, setChatOpen] = useState(false);

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
      {/* Header row with refresh button */}
      <div
        className="flex items-center justify-end"
        style={{ marginTop: -4, marginBottom: 4 }}
      >
        <button
          onClick={refresh}
          disabled={isFetching}
          title="Refresh analysis"
          style={{
            background: 'none',
            border: '1px solid var(--border-primary)',
            borderRadius: 4,
            padding: '3px 7px',
            cursor: isFetching ? 'not-allowed' : 'pointer',
            color: 'var(--text-muted)',
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            opacity: isFetching ? 0.5 : 1,
            transition: 'opacity 0.2s',
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              animation: isFetching ? 'spin 1s linear infinite' : 'none',
            }}
          >
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
          </svg>
          {isFetching ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

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

      {/* Chat toggle */}
      <div style={{ marginTop: 12 }}>
        <button
          onClick={() => setChatOpen(!chatOpen)}
          style={{
            width: '100%',
            background: 'none',
            border: '1px solid var(--border-primary)',
            borderRadius: 6,
            padding: '8px 12px',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            fontSize: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <span>{chatOpen ? 'Close chat' : 'Ask a question'}</span>
          <span style={{ fontSize: 10, opacity: 0.6 }}>{chatOpen ? '▲' : '▼'}</span>
        </button>

        {chatOpen && <ChatPanel />}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Card>
  );
}
