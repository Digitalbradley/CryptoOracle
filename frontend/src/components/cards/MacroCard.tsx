import { useMacro } from '../../hooks/useMacro';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';

const SUB_SIGNALS = [
  { key: 'liquidity_score' as const, label: 'Liquidity', color: '#818cf8' },
  { key: 'treasury_score' as const, label: 'Treasury', color: '#a78bfa' },
  { key: 'dollar_score' as const, label: 'Dollar', color: '#34d399' },
  { key: 'oil_score' as const, label: 'Oil', color: '#fbbf24' },
  { key: 'carry_trade_score' as const, label: 'Carry Trade', color: '#f87171' },
];

function regimeColor(regime: string | null): string {
  if (!regime) return 'var(--text-muted)';
  switch (regime) {
    case 'risk_on':
    case 'easing':
      return 'var(--signal-bullish)';
    case 'risk_off':
    case 'tightening':
    case 'carry_unwind':
      return 'var(--signal-bearish)';
    default:
      return 'var(--signal-neutral)';
  }
}

function regimeLabel(regime: string | null): string {
  if (!regime) return 'N/A';
  return regime.replace(/_/g, ' ').toUpperCase();
}

function stressColor(stress: number): string {
  if (stress >= 0.7) return 'var(--severity-critical)';
  if (stress >= 0.4) return 'var(--severity-warning)';
  return 'var(--signal-neutral)';
}

export default function MacroCard() {
  const { data, isLoading } = useMacro();

  if (isLoading) {
    return (
      <Card title="Macro Liquidity" layerColor="var(--layer-macro)">
        <div className="space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-full" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  if (!data || data.status === 'no_data') {
    return (
      <Card title="Macro Liquidity" layerColor="var(--layer-macro)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No macro signal data</p>
      </Card>
    );
  }

  const macroScore = parseScore(data.macro_score);
  const carryStress = parseScore(data.data_points.carry_stress);
  const confidence = parseScore(data.regime_confidence);

  return (
    <Card title="Macro Liquidity" layerColor="var(--layer-macro)">
      {/* Regime + Score header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            Regime
          </span>
          <div className="flex items-center gap-1.5">
            <span
              className="font-mono text-xs font-semibold"
              style={{ color: regimeColor(data.regime) }}
            >
              {regimeLabel(data.regime)}
            </span>
            {confidence > 0 && (
              <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
                ({(confidence * 100).toFixed(0)}%)
              </span>
            )}
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            Score
          </span>
          <div
            className="font-mono text-lg font-bold"
            style={{ color: macroScore >= 0 ? 'var(--signal-bullish)' : 'var(--signal-bearish)' }}
          >
            {macroScore >= 0 ? '+' : ''}{macroScore.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Macro composite bar */}
      <LayerBar label="Macro" score={macroScore} color="var(--layer-macro)" />

      {/* Sub-signal bars */}
      <div className="mt-2 space-y-0.5">
        {SUB_SIGNALS.map((sig) => {
          const score = parseScore(data.sub_signals[sig.key]);
          return (
            <LayerBar key={sig.key} label={sig.label} score={score} color={sig.color} />
          );
        })}
      </div>

      {/* Key data points */}
      <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5">
        <DataPoint label="DXY" value={data.data_points.dxy_value} />
        <DataPoint label="VIX" value={data.data_points.vix_value} />
        <DataPoint label="2s10s" value={data.data_points.yield_curve_2s10s} suffix="%" />
        <DataPoint label="WTI" value={data.data_points.wti_price} prefix="$" />
        <DataPoint label="USD/JPY" value={data.data_points.usdjpy_value} />
        <DataPoint label="M2 YoY" value={data.data_points.m2_yoy_pct} suffix="%" />
      </div>

      {/* Carry stress indicator */}
      <div className="mt-3">
        <div className="flex justify-between mb-0.5">
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Carry Stress</span>
          <span className="font-mono text-[10px]" style={{ color: stressColor(carryStress) }}>
            {carryStress.toFixed(2)}
          </span>
        </div>
        <div className="h-1.5 rounded-full" style={{ backgroundColor: 'var(--bg-elevated)' }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, carryStress * 100)}%`,
              backgroundColor: stressColor(carryStress),
            }}
          />
        </div>
      </div>
    </Card>
  );
}

function DataPoint({
  label,
  value,
  prefix = '',
  suffix = '',
}: {
  label: string;
  value: string | null;
  prefix?: string;
  suffix?: string;
}) {
  const num = parseScore(value);
  return (
    <div className="flex justify-between items-center">
      <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span className="font-mono text-[11px]" style={{ color: 'var(--text-primary)' }}>
        {value ? `${prefix}${num.toFixed(2)}${suffix}` : '—'}
      </span>
    </div>
  );
}
