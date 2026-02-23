import { useOnchain } from '../../hooks/useOnchain';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';
import Tooltip from '../ui/Tooltip';

const fmtCompact = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

function Metric({ label, tip, value, suffix }: { label: string; tip?: string; value: string; suffix?: string }) {
  return (
    <div className="flex justify-between items-center py-0.5">
      <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
        {tip ? <Tooltip text={tip}>{label}</Tooltip> : label}
      </span>
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
          <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
            <Tooltip text="Net coins moving to/from exchanges. Outflow = accumulation (bullish)">Exchange Netflow</Tooltip>
          </span>
          <span
            className="font-mono text-xs"
            style={{ color: isOutflow ? 'var(--signal-bullish)' : 'var(--signal-bearish)' }}
          >
            {isOutflow ? '↗ Outflow' : '↙ Inflow'} {fmtCompact.format(Math.abs(netflow))}
          </span>
        </div>

        <Metric
          label="Whale Txns"
          tip="Large holder transactions (>$100K). High activity = potential volatility"
          value={metrics.whale_transactions_count != null ? String(metrics.whale_transactions_count) : '—'}
        />
        <Metric
          label="NUPL"
          tip="Net Unrealized Profit/Loss — aggregate holder profitability (0 to 1)"
          value={metrics.nupl != null ? parseScore(metrics.nupl).toFixed(3) : '—'}
        />
        <Metric
          label="MVRV Z-Score"
          tip="Market Value vs Realized Value. Above 1.5 = overvalued, below -1 = undervalued"
          value={metrics.mvrv_zscore != null ? parseScore(metrics.mvrv_zscore).toFixed(2) : '—'}
        />
        <Metric
          label="SOPR"
          tip="Spent Output Profit Ratio. Above 1 = holders selling at profit"
          value={metrics.sopr != null ? parseScore(metrics.sopr).toFixed(3) : '—'}
        />
      </div>
    </Card>
  );
}
