import { usePrices } from '../../hooks/usePrices';
import { useSymbol } from '../../hooks/useSymbol';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import Skeleton from '../ui/Skeleton';

const fmt = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const fmtVol = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

export default function PriceCard() {
  const { symbol } = useSymbol();
  const { data, isLoading } = usePrices();

  if (isLoading) {
    return (
      <Card>
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-24 mt-2" />
      </Card>
    );
  }

  const candles = data?.data;
  if (!candles || candles.length === 0) {
    return (
      <Card>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No price data</p>
      </Card>
    );
  }

  const last = candles[candles.length - 1];
  const first = candles[0];
  const close = parseScore(last.close);
  const open = parseScore(first.open);
  const changePct = open !== 0 ? ((close - open) / open) * 100 : 0;
  const isPositive = changePct >= 0;

  const high = Math.max(...candles.map((c) => parseScore(c.high)));
  const low = Math.min(...candles.map((c) => parseScore(c.low)));
  const volume = parseScore(last.volume);

  const displaySymbol = symbol.replace('-', '/');

  return (
    <Card>
      <div className="flex items-baseline justify-between">
        <div>
          <span
            className="text-xs font-semibold uppercase tracking-wider"
            style={{ color: 'var(--text-secondary)' }}
          >
            {displaySymbol}
          </span>
          <div
            className="font-mono text-2xl font-bold"
            style={{ color: 'var(--text-primary)' }}
          >
            ${fmt.format(close)}
          </div>
        </div>
        <div className="text-right">
          <span
            className="font-mono text-sm font-semibold"
            style={{ color: isPositive ? 'var(--signal-bullish)' : 'var(--signal-bearish)' }}
          >
            {isPositive ? '▲' : '▼'} {isPositive ? '+' : ''}{changePct.toFixed(2)}%
          </span>
        </div>
      </div>

      <div className="flex gap-4 mt-2">
        <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
          H {fmt.format(high)}
        </span>
        <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
          L {fmt.format(low)}
        </span>
        <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
          Vol {fmtVol.format(volume)}
        </span>
      </div>
    </Card>
  );
}
