import { useEffect, useState } from 'react';
import { useSymbol } from '../hooks/useSymbol';
import { usePrices } from '../hooks/usePrices';
import { parseScore } from '../types/api';
import type { SymbolId } from '../types/api';

const SYMBOLS: { id: SymbolId; label: string }[] = [
  { id: 'BTC-USDT', label: 'BTC' },
  { id: 'ETH-USDT', label: 'ETH' },
  { id: 'XRP-USDT', label: 'XRP' },
];

const priceFmt = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export default function TopBar() {
  const { symbol, setSymbol } = useSymbol();
  const { data } = usePrices();
  const [clock, setClock] = useState('');

  useEffect(() => {
    const tick = () => {
      setClock(new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'UTC',
      }) + ' UTC');
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const candles = data?.data;
  const lastClose = candles?.length ? parseScore(candles[candles.length - 1].close) : null;
  const firstOpen = candles?.length ? parseScore(candles[0].open) : null;
  const changePct = lastClose && firstOpen && firstOpen !== 0
    ? ((lastClose - firstOpen) / firstOpen) * 100
    : null;

  return (
    <header
      className="sticky top-0 z-30 flex items-center justify-between px-3 h-12"
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
      }}
    >
      {/* Left: Logo + symbol tabs */}
      <div className="flex items-center gap-3">
        {/* Logo */}
        <span className="text-base font-bold" style={{ color: 'var(--accent-gold)' }}>
          ☽
        </span>

        {/* Symbol tabs */}
        <div className="flex gap-1">
          {SYMBOLS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSymbol(s.id)}
              className="px-2.5 py-1 text-xs font-semibold rounded transition-colors"
              style={{
                backgroundColor: symbol === s.id ? 'var(--accent-gold-dim)' : 'transparent',
                color: symbol === s.id ? 'var(--accent-gold)' : 'var(--text-muted)',
                border: 'none',
                cursor: 'pointer',
                minHeight: '32px',
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Right: Price ticker + clock */}
      <div className="flex items-center gap-3">
        {lastClose != null && (
          <div className="flex items-baseline gap-1.5">
            <span className="font-mono text-sm font-bold" style={{ color: 'var(--text-primary)' }}>
              ${priceFmt.format(lastClose)}
            </span>
            {changePct != null && (
              <span
                className="font-mono text-xs"
                style={{ color: changePct >= 0 ? 'var(--signal-bullish)' : 'var(--signal-bearish)' }}
              >
                {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
              </span>
            )}
          </div>
        )}
        <span className="font-mono text-[10px] hidden sm:inline" style={{ color: 'var(--text-muted)' }}>
          {clock}
        </span>
      </div>
    </header>
  );
}
