import { useSentiment } from '../../hooks/useSentiment';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';
import Tooltip from '../ui/Tooltip';

function fgColor(index: number): string {
  if (index <= 25) return 'var(--signal-bearish)';
  if (index <= 45) return 'var(--severity-warning)';
  if (index <= 55) return 'var(--signal-neutral)';
  if (index <= 75) return 'var(--signal-bullish)';
  return 'var(--signal-bullish)';
}

export default function SentimentCard() {
  const { data, isLoading } = useSentiment();

  if (isLoading) {
    return (
      <Card title="Sentiment" layerColor="var(--layer-sentiment)">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-8 w-16 mt-2 mx-auto" />
      </Card>
    );
  }

  const sent = data?.sentiment;
  if (!sent) {
    return (
      <Card title="Sentiment" layerColor="var(--layer-sentiment)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No sentiment data</p>
      </Card>
    );
  }

  const score = parseScore(sent.sentiment_score);
  const fgIndex = sent.fear_greed_index ?? 50;
  const label = sent.fear_greed_label || 'Unknown';

  return (
    <Card title="Sentiment" layerColor="var(--layer-sentiment)">
      <LayerBar label="Score" score={score} color="var(--layer-sentiment)" />

      <div className="mt-3 text-center">
        <p className="text-[10px] mb-1" style={{ color: 'var(--text-muted)' }}>
          <Tooltip text="Market sentiment (0-100). 0 = extreme fear, 100 = extreme greed. Contrarian — fear often means buying opportunity">
            Fear & Greed Index
          </Tooltip>
        </p>
        <div
          className="font-mono text-3xl font-bold"
          style={{ color: fgColor(fgIndex) }}
        >
          {fgIndex}
        </div>
        <p className="text-xs mt-0.5" style={{ color: fgColor(fgIndex) }}>
          {label}
        </p>
      </div>

      {/* Fear/greed bar */}
      <div className="mt-3 relative h-2 rounded-full overflow-hidden"
        style={{
          background: 'linear-gradient(to right, var(--signal-bearish), var(--severity-warning), var(--signal-neutral), var(--signal-bullish))',
        }}
      >
        <div
          className="absolute top-[-2px] w-3 h-3 rounded-full border-2"
          style={{
            left: `calc(${fgIndex}% - 6px)`,
            backgroundColor: 'var(--bg-void)',
            borderColor: fgColor(fgIndex),
          }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-[9px]" style={{ color: 'var(--signal-bearish)' }}>Fear</span>
        <span className="text-[9px]" style={{ color: 'var(--signal-bullish)' }}>Greed</span>
      </div>
    </Card>
  );
}
