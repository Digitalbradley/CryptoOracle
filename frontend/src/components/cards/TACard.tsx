import { useState } from 'react';
import { useTASignals } from '../../hooks/useTASignals';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';
import Tooltip from '../ui/Tooltip';

function Indicator({ label, tip, value, color }: { label: string; tip?: string; value: string | null; color?: string }) {
  const num = parseScore(value);
  return (
    <div className="flex justify-between items-center py-0.5">
      <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
        {tip ? <Tooltip text={tip}>{label}</Tooltip> : label}
      </span>
      <span
        className="font-mono text-xs"
        style={{ color: color || 'var(--text-primary)' }}
      >
        {value != null ? num.toFixed(2) : '—'}
      </span>
    </div>
  );
}

function rsiColor(val: number): string {
  if (val > 70) return 'var(--signal-bearish)';
  if (val < 30) return 'var(--signal-bullish)';
  return 'var(--text-primary)';
}

export default function TACard() {
  const { data, isLoading } = useTASignals();
  const [expanded, setExpanded] = useState(false);

  if (isLoading) {
    return (
      <Card title="Technical Analysis" layerColor="var(--layer-ta)">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </Card>
    );
  }

  const ind = data?.indicators;
  if (!ind) {
    return (
      <Card title="Technical Analysis" layerColor="var(--layer-ta)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No TA data available</p>
      </Card>
    );
  }

  const taScore = parseScore(ind.ta_score);
  const rsi14 = parseScore(ind.rsi_14);

  return (
    <Card title="Technical Analysis" layerColor="var(--layer-ta)">
      <LayerBar label="TA Score" score={taScore} color="var(--layer-ta)" />

      <div className="mt-3 space-y-0.5">
        <Indicator label="RSI (14)" tip="Relative Strength Index — momentum (0-100). Above 70 = overbought, below 30 = oversold" value={ind.rsi_14} color={rsiColor(rsi14)} />
        <Indicator label="MACD" tip="Moving Average Convergence Divergence — trend momentum indicator" value={ind.macd_line} />
        <Indicator label="MACD Signal" tip="MACD signal line — crossovers indicate trend changes" value={ind.macd_signal} />
        <Indicator
          label="MACD Hist"
          tip="MACD histogram — difference between MACD and signal. Positive = bullish momentum"
          value={ind.macd_histogram}
          color={parseScore(ind.macd_histogram) >= 0 ? 'var(--signal-bullish)' : 'var(--signal-bearish)'}
        />
      </div>

      {expanded && (
        <div className="mt-2 space-y-0.5">
          <Indicator label="SMA 20" tip="Simple Moving Average (20 periods) — short-term trend" value={ind.sma_20} />
          <Indicator label="SMA 50" tip="Simple Moving Average (50 periods) — medium-term trend" value={ind.sma_50} />
          <Indicator label="SMA 200" tip="Simple Moving Average (200 periods) — long-term trend" value={ind.sma_200} />
          <Indicator label="BB Upper" tip="Bollinger Band upper — price near here = potentially overbought" value={ind.bb_upper} />
          <Indicator label="BB Middle" tip="Bollinger Band middle (20-period SMA)" value={ind.bb_middle} />
          <Indicator label="BB Lower" tip="Bollinger Band lower — price near here = potentially oversold" value={ind.bb_lower} />
          <Indicator label="Stoch K" tip="Stochastic oscillator (0-100). Above 80 = overbought, below 20 = oversold" value={ind.stoch_k} />
          <Indicator label="Stoch D" tip="Stochastic signal line — smoothed version of K" value={ind.stoch_d} />
          <Indicator label="ATR (14)" tip="Average True Range — measures price volatility (higher = more volatile)" value={ind.atr_14} />
        </div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-2 text-[11px] w-full text-center"
        style={{ color: 'var(--accent-gold)', cursor: 'pointer', background: 'none', border: 'none' }}
      >
        {expanded ? 'Show less' : 'Show more'}
      </button>
    </Card>
  );
}
