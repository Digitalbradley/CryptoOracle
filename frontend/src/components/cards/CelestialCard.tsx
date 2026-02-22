import { useCelestial } from '../../hooks/useCelestial';
import { parseScore } from '../../types/api';
import Card from '../ui/Card';
import LayerBar from '../ui/LayerBar';
import Skeleton from '../ui/Skeleton';

const MOON_EMOJI: Record<string, string> = {
  'New Moon': '🌑',
  'Waxing Crescent': '🌒',
  'First Quarter': '🌓',
  'Waxing Gibbous': '🌔',
  'Full Moon': '🌕',
  'Waning Gibbous': '🌖',
  'Last Quarter': '🌗',
  'Waning Crescent': '🌘',
};

const PLANETS = [
  { key: 'mercury_retrograde' as const, label: 'Mercury' },
  { key: 'venus_retrograde' as const, label: 'Venus' },
  { key: 'mars_retrograde' as const, label: 'Mars' },
  { key: 'jupiter_retrograde' as const, label: 'Jupiter' },
  { key: 'saturn_retrograde' as const, label: 'Saturn' },
];

export default function CelestialCard() {
  const { data, isLoading } = useCelestial();

  if (isLoading) {
    return (
      <Card title="Celestial" layerColor="var(--layer-celestial)">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </Card>
    );
  }

  const state = data?.state;
  if (!state) {
    return (
      <Card title="Celestial" layerColor="var(--layer-celestial)">
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>No celestial data</p>
      </Card>
    );
  }

  const score = parseScore(state.celestial_score);
  const moonName = state.lunar_phase_name || 'Unknown';
  const moonEmoji = MOON_EMOJI[moonName] || '🌙';
  const illumination = parseScore(state.lunar_illumination);

  return (
    <Card title="Celestial" layerColor="var(--layer-celestial)">
      <LayerBar label="Score" score={score} color="var(--layer-celestial)" />

      {/* Moon phase */}
      <div className="mt-3 flex items-center gap-2">
        <span className="text-2xl">{moonEmoji}</span>
        <div>
          <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
            {moonName}
          </p>
          <p className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
            {illumination.toFixed(0)}% illumination
          </p>
        </div>
      </div>

      {/* Retrogrades */}
      <div className="mt-3">
        <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>
          Retrogrades ({state.retrograde_count})
        </p>
        <div className="flex flex-wrap gap-1.5">
          {PLANETS.map((p) => {
            const isRetro = state[p.key];
            return (
              <span
                key={p.key}
                className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor: isRetro ? 'var(--signal-bearish)' : 'var(--bg-elevated)',
                  color: isRetro ? 'var(--bg-void)' : 'var(--text-muted)',
                  opacity: isRetro ? 1 : 0.5,
                }}
              >
                {p.label} {isRetro ? 'Rx' : '—'}
              </span>
            );
          })}
        </div>
      </div>

      {/* Eclipse flags */}
      {(state.is_lunar_eclipse || state.is_solar_eclipse) && (
        <div className="mt-2">
          {state.is_lunar_eclipse && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'var(--severity-warning)', color: 'var(--bg-void)' }}>
              Lunar Eclipse
            </span>
          )}
          {state.is_solar_eclipse && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full ml-1"
              style={{ backgroundColor: 'var(--severity-critical)', color: 'var(--bg-void)' }}>
              Solar Eclipse
            </span>
          )}
        </div>
      )}

      {/* Days to next moon events */}
      <div className="flex gap-4 mt-2">
        <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
          New ☽ {parseScore(state.days_to_next_new_moon).toFixed(0)}d
        </span>
        <span className="font-mono text-[10px]" style={{ color: 'var(--text-muted)' }}>
          Full ☽ {parseScore(state.days_to_next_full_moon).toFixed(0)}d
        </span>
      </div>
    </Card>
  );
}
