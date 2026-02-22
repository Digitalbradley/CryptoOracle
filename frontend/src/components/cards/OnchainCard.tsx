import { useOnchain } from '../../hooks/useOnchain';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';

const fmtCompact = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

function Metric({ label, value, suffix }: { label: string; value: string; suffix?: string }) {
  return (
    <div className="flex justify-between items-center py-0.5">
      <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span className="font-mono text-xs" style={{ color: 'var(--text-primary)' }}>
        {value}{suffix || ''}
      </span>
    </div>
  );
}

export default function OnchainCard() {
  const { data, isLoading } = useOnchain();

  if (isLoading) {
    return (
      <Card title="On-Chain" layerColor="var(--layer-onchain)">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </Card>
    );
  }

  const metrics = data?.metrics;
  if (!metrics) {
    return (
      <Card title="On-Chain" layerColor="var(--layer-onchain)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No on-chain data</p>
      </Card>
    );
  }

  const score = parseScore(metrics.onchain_score);
  const netflow = parseScore(metrics.exchange_netflow);
  const isOutflow = netflow < 0;

  return (
    <Card title="On-Chain" layerColor="var(--layer-onchain)">
      <LayerBar label="Score" score={score} color="var(--layer-onchain)" />

      <div className="mt-3 space-y-0.5">
        <div className="flex justify-between items-center py-0.5">
          <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>Exchange Netflow</span>
          <span
            className="font-mono text-xs"
            style={{ color: isOutflow ? 'var(--signal-bullish)' : 'var(--signal-bearish)' }}
          >
            {isOutflow ? '↗ Outflow' : '↙ Inflow'} {fmtCompact.format(Math.abs(netflow))}
          </span>
        </div>

        <Metric
          label="Whale Txns"
          value={metrics.whale_transactions_count != null ? String(metrics.whale_transactions_count) : '—'}
        />
        <Metric
          label="NUPL"
          value={metrics.nupl != null ? parseScore(metrics.nupl).toFixed(3) : '—'}
        />
        <Metric
          label="MVRV Z-Score"
          value={metrics.mvrv_zscore != null ? parseScore(metrics.mvrv_zscore).toFixed(2) : '—'}
        />
        <Metric
          label="SOPR"
          value={metrics.sopr != null ? parseScore(metrics.sopr).toFixed(3) : '—'}
        />
      </div>
    </Card>
  );
}
