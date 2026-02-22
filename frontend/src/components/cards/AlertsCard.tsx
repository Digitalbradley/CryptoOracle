import { useState } from 'react';
import { useAlerts, useAcknowledgeAlert } from '../../hooks/useAlerts';
import Card from '../ui/Card';
import SeverityDot from '../ui/SeverityDot';
import Skeleton from '../ui/Skeleton';

function timeAgo(iso: string | null): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function AlertsCard() {
  const { data, isLoading } = useAlerts();
  const acknowledge = useAcknowledgeAlert();
  const [showAll, setShowAll] = useState(false);

  if (isLoading) {
    return (
      <Card title="Active Alerts">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </Card>
    );
  }

  const alerts = data?.alerts ?? [];

  if (alerts.length === 0) {
    return (
      <Card title="Active Alerts">
        <p className="text-xs text-center py-2" style={{ color: 'var(--text-muted)' }}>
          No active alerts
        </p>
      </Card>
    );
  }

  const visible = showAll ? alerts : alerts.slice(0, 5);

  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <h3
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: 'var(--text-secondary)' }}
        >
          Active Alerts
        </h3>
        <span
          className="font-mono text-[10px] px-1.5 py-0.5 rounded-full"
          style={{
            backgroundColor: 'var(--accent-gold-dim)',
            color: 'var(--accent-gold)',
          }}
        >
          {data?.count ?? 0}
        </span>
      </div>

      <div className="space-y-2">
        {visible.map((alert) => (
          <div
            key={alert.id}
            className="flex items-start gap-2 p-2 rounded-lg"
            style={{ backgroundColor: 'var(--bg-elevated)' }}
          >
            <SeverityDot severity={alert.severity} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                {alert.title}
              </p>
              <p className="text-[11px] truncate" style={{ color: 'var(--text-secondary)' }}>
                {alert.description}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
                  {timeAgo(alert.triggered_at)}
                </span>
                {alert.symbol && (
                  <span
                    className="text-[9px] px-1 rounded"
                    style={{
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {alert.symbol}
                  </span>
                )}
              </div>
            </div>
            <button
              onClick={() => acknowledge.mutate(alert.id)}
              className="text-[10px] px-2 py-1 rounded shrink-0"
              style={{
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                background: 'none',
              }}
              disabled={acknowledge.isPending}
            >
              Ack
            </button>
          </div>
        ))}
      </div>

      {alerts.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-2 text-[11px] w-full text-center"
          style={{ color: 'var(--accent-gold)', cursor: 'pointer', background: 'none', border: 'none' }}
        >
          {showAll ? 'Show less' : `Show all ${alerts.length}`}
        </button>
      )}
    </Card>
  );
}
