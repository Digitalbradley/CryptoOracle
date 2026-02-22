import { useConfluence } from '../../hooks/useConfluence';
import { useWeights } from '../../hooks/useWeights';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import ScoreGauge from '../ui/ScoreGauge';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';

const LAYERS = [
  { key: 'ta_score' as const, label: 'Technical', color: 'var(--layer-ta)', weightKey: 'ta' as const },
  { key: 'onchain_score' as const, label: 'On-Chain', color: 'var(--layer-onchain)', weightKey: 'onchain' as const },
  { key: 'celestial_score' as const, label: 'Celestial', color: 'var(--layer-celestial)', weightKey: 'celestial' as const },
  { key: 'numerology_score' as const, label: 'Numerology', color: 'var(--layer-numerology)', weightKey: 'numerology' as const },
  { key: 'sentiment_score' as const, label: 'Sentiment', color: 'var(--layer-sentiment)', weightKey: 'sentiment' as const },
  { key: 'political_score' as const, label: 'Political', color: 'var(--layer-political)', weightKey: 'political' as const },
];

export default function ConfluenceCard() {
  const { data: confluence, isLoading: cLoading } = useConfluence();
  const { data: weightsData } = useWeights();

  if (cLoading) {
    return (
      <Card title="Confluence">
        <div className="space-y-3">
          <Skeleton className="h-12 w-24 mx-auto" />
          <Skeleton className="h-2 w-full" />
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  if (!confluence) {
    return (
      <Card title="Confluence">
        <p className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
          No confluence data available
        </p>
      </Card>
    );
  }

  const weights = weightsData?.weights;

  return (
    <Card title="Confluence">
      <ScoreGauge
        score={confluence.composite_score}
        signalStrength={confluence.signal_strength}
        alignmentCount={confluence.alignment_count}
      />

      <div className="mt-4 space-y-0.5">
        {LAYERS.map((layer) => {
          const raw = confluence.scores[layer.key];
          const score = typeof raw === 'number' ? raw : parseScore(raw as string | null);
          return (
            <LayerBar
              key={layer.key}
              label={layer.label}
              score={score}
              color={layer.color}
              weight={weights?.[layer.weightKey]}
            />
          );
        })}
      </div>
    </Card>
  );
}
