import { useXaiScore, useXaiCalendar } from '../../hooks/useXai';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';
import Tooltip from '../ui/Tooltip';

const PHASE_LABELS: Record<string, string> = {
  pre_adoption: 'Pre-Adoption',
  early_adoption: 'Early Adoption',
  accelerating: 'Accelerating',
  institutional_scale: 'Institutional',
  stability_approaching: 'Stability',
  stable_utility: 'Stable Utility',
};

const PHASE_ORDER = [
  'pre_adoption',
  'early_adoption',
  'accelerating',
  'institutional_scale',
  'stability_approaching',
  'stable_utility',
];

function phaseIndex(phase: string | null): number {
  if (!phase) return 0;
  const idx = PHASE_ORDER.indexOf(phase);
  return idx >= 0 ? idx : 0;
}

function formatUsd(value: string | null): string {
  if (!value) return '—';
  const num = parseFloat(value);
  if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(0)}M`;
  if (num >= 1_000) return `$${(num / 1_000).toFixed(0)}K`;
  return `$${num.toFixed(0)}`;
}

function impactColor(impact: string | null): string {
  if (impact === 'high') return 'var(--accent-gold)';
  if (impact === 'medium') return 'var(--text-secondary)';
  return 'var(--text-muted)';
}

export default function XaiCard() {
  const { data, isLoading } = useXaiScore();
  const { data: calendarData } = useXaiCalendar();

  if (isLoading) {
    return (
      <Card title="XRP Adoption (XAI)" layerColor="#6366f1">
        <div className="space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </Card>
    );
  }

  if (!data || data.status === 'no_data') {
    return (
      <Card title="XRP Adoption (XAI)" layerColor="#6366f1">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          No XAI data — run Phase 6 bootstrap
        </p>
      </Card>
    );
  }

  const xaiScore = parseScore(data.xai_score);
  const ratio = parseScore(data.utility_to_speculation_ratio);
  const rlusdCap = data.rlusd_market_cap;
  const phase = data.adoption_phase || 'pre_adoption';
  const pIdx = phaseIndex(phase);

  return (
    <Card title="XRP Adoption (XAI)" layerColor="#6366f1">
      {/* Phase + Score header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            <Tooltip text="Current stage in the XRP institutional adoption lifecycle">Phase</Tooltip>
          </span>
          <div
            className="font-mono text-xs font-semibold"
            style={{ color: '#818cf8' }}
          >
            {PHASE_LABELS[phase] || phase.replace(/_/g, ' ').toUpperCase()}
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            XAI Score
          </span>
          <div
            className="font-mono text-lg font-bold"
            style={{ color: xaiScore >= 0 ? 'var(--signal-bullish)' : 'var(--signal-bearish)' }}
          >
            {xaiScore >= 0 ? '+' : ''}{xaiScore.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Phase progress bar */}
      <div className="mb-3">
        <div className="flex justify-between mb-1">
          {PHASE_ORDER.map((p, i) => (
            <span
              key={p}
              className="text-[8px]"
              style={{ color: i <= pIdx ? '#818cf8' : 'var(--text-muted)', fontWeight: i === pIdx ? 700 : 400 }}
            >
              {i === 0 ? 'Pre' : i === 1 ? 'Early' : i === 2 ? 'Accel' : i === 3 ? 'Inst.' : i === 4 ? 'Stab.' : 'Util.'}
            </span>
          ))}
        </div>
        <div className="h-1.5 rounded-full" style={{ backgroundColor: 'var(--bg-elevated)' }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${((pIdx + 1) / PHASE_ORDER.length) * 100}%`,
              backgroundColor: '#818cf8',
            }}
          />
        </div>
      </div>

      {/* Utility/Speculation Ratio */}
      <div className="mb-3">
        <div className="flex justify-between mb-0.5">
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
            <Tooltip text="When utility volume exceeds speculation volume (ratio > 1.0), XRP reaches the stability inflection point">
              Utility/Speculation Ratio
            </Tooltip>
          </span>
          <span className="font-mono text-[10px]" style={{ color: ratio >= 1 ? 'var(--signal-bullish)' : 'var(--text-secondary)' }}>
            {ratio.toFixed(4)} / 1.0
          </span>
        </div>
        <div className="h-1.5 rounded-full" style={{ backgroundColor: 'var(--bg-elevated)' }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, ratio * 100)}%`,
              backgroundColor: ratio >= 1 ? 'var(--signal-bullish)' : '#6366f1',
            }}
          />
        </div>
      </div>

      {/* Sub-signal bars */}
      <div className="space-y-0.5">
        <LayerBar
          label="On-Chain"
          tooltip="XRPL utility metrics: RLUSD supply, trust lines, utility/speculation ratio"
          score={parseScore(data.onchain_utility_score)}
          color="#818cf8"
        />
        <LayerBar
          label="Partners"
          tooltip="Weighted score of Ripple's institutional partnership pipeline"
          score={parseScore(data.partnership_deployment_score)}
          color="#a78bfa"
        />
        {data.policy_pipeline_score ? (
          <LayerBar
            label="Policy"
            tooltip="Regulatory and policy environment favorability"
            score={parseScore(data.policy_pipeline_score)}
            color="#c084fc"
          />
        ) : (
          <div className="flex items-center gap-2 py-1">
            <span className="text-xs w-20 shrink-0" style={{ color: 'var(--text-muted)' }}>Policy</span>
            <span className="text-[10px] italic" style={{ color: 'var(--text-muted)' }}>Phase B</span>
          </div>
        )}
        {data.personnel_intelligence_score ? (
          <LayerBar
            label="Personnel"
            tooltip="Key decision-maker sentiment analysis"
            score={parseScore(data.personnel_intelligence_score)}
            color="#e879f9"
          />
        ) : (
          <div className="flex items-center gap-2 py-1">
            <span className="text-xs w-20 shrink-0" style={{ color: 'var(--text-muted)' }}>Personnel</span>
            <span className="text-[10px] italic" style={{ color: 'var(--text-muted)' }}>Phase C</span>
          </div>
        )}
      </div>

      {/* Key metrics */}
      <div className="mt-3">
        <p className="text-[10px] uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
          Key Metrics
        </p>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
          <MetricItem label="RLUSD Supply" value={formatUsd(rlusdCap)} />
          <MetricItem label="Partners" value={data.active_partnership_count != null ? String(data.active_partnership_count) : '—'} />
          <MetricItem label="In Production" value={data.partnerships_in_production != null ? String(data.partnerships_in_production) : '—'} />
          <MetricItem label="U/S Ratio" value={ratio > 0 ? ratio.toFixed(4) : '—'} />
        </div>
      </div>

      {/* Upcoming events */}
      {calendarData && calendarData.events.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-muted)' }}>
            Upcoming Events
          </p>
          <div className="space-y-1">
            {calendarData.events.slice(0, 3).map((ev) => (
              <div key={ev.id} className="flex items-center justify-between">
                <span className="text-[10px] truncate" style={{ color: impactColor(ev.potential_impact), maxWidth: '70%' }}>
                  {ev.event_name}
                </span>
                <span className="text-[10px] font-mono shrink-0" style={{ color: 'var(--text-muted)' }}>
                  {ev.event_date}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{label}</span>
      <span className="font-mono text-[11px]" style={{ color: 'var(--text-primary)' }}>{value}</span>
    </div>
  );
}
