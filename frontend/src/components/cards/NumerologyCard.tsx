import { useNumerology } from '../../hooks/useNumerology';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';

export default function NumerologyCard() {
  const { data, isLoading } = useNumerology();

  if (isLoading) {
    return (
      <Card title="Numerology" layerColor="var(--layer-numerology)">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-8 w-16 mt-2 mx-auto" />
      </Card>
    );
  }

  const num = data?.numerology;
  if (!num) {
    return (
      <Card title="Numerology" layerColor="var(--layer-numerology)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No numerology data</p>
      </Card>
    );
  }

  const score = parseScore(num.numerology_score);

  return (
    <Card title="Numerology" layerColor="var(--layer-numerology)">
      <LayerBar label="Score" score={score} color="var(--layer-numerology)" />

      <div className="mt-3 text-center">
        {/* Universal day number */}
        <div
          className={`font-mono text-3xl font-bold inline-block ${num.is_master_number ? 'gold-pulse' : ''}`}
          style={{
            color: num.is_master_number ? 'var(--accent-gold)' : 'var(--text-primary)',
          }}
        >
          {num.universal_day_number}
        </div>
        <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
          Universal Day{num.is_master_number ? ' • Master Number' : ''}
        </p>
      </div>

      <div className="flex justify-around mt-3">
        <div className="text-center">
          <div className="font-mono text-sm" style={{ color: 'var(--text-primary)' }}>
            {num.cycle_confluence_count}
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Cycle Hits</div>
        </div>
        <div className="text-center">
          <div className="font-mono text-sm" style={{ color: 'var(--text-primary)' }}>
            {num.price_47_appearances}
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>47 Appearances</div>
        </div>
        <div className="text-center">
          <div className="font-mono text-sm" style={{ color: 'var(--text-primary)' }}>
            {num.date_digit_sum}
          </div>
          <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Digit Sum</div>
        </div>
      </div>
    </Card>
  );
}
