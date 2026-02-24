// ---------- Shared ----------
export type SymbolId = 'BTC-USDT' | 'ETH-USDT' | 'XRP-USDT';
export type Timeframe = '1h' | '4h' | '1d';
export type LayerName =
  | 'ta'
  | 'onchain'
  | 'celestial'
  | 'numerology'
  | 'sentiment'
  | 'political'
  | 'macro';

export type SignalStrength =
  | 'STRONG BUY'
  | 'BUY'
  | 'NEUTRAL'
  | 'SELL'
  | 'STRONG SELL';

/** Safely parse a numeric string from the API into a number. Returns 0 for null/undefined/NaN. */
export function parseScore(value: string | null | undefined): number {
  if (value == null) return 0;
  const n = parseFloat(value);
  return Number.isNaN(n) ? 0 : n;
}

// ---------- Price ----------
export interface Candle {
  timestamp: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export interface PriceResponse {
  symbol: string;
  timeframe: string;
  count: number;
  data: Candle[];
}

// ---------- TA Indicators ----------
export interface TAIndicators {
  timestamp: string;
  symbol: string;
  timeframe: string;
  rsi_14: string | null;
  rsi_7: string | null;
  macd_line: string | null;
  macd_signal: string | null;
  macd_histogram: string | null;
  stoch_k: string | null;
  stoch_d: string | null;
  sma_20: string | null;
  sma_50: string | null;
  sma_200: string | null;
  ema_12: string | null;
  ema_26: string | null;
  bb_upper: string | null;
  bb_middle: string | null;
  bb_lower: string | null;
  atr_14: string | null;
  ta_score: string | null;
}

export interface TAResponse {
  symbol: string;
  timeframe: string;
  indicators: TAIndicators | null;
}

// ---------- Celestial ----------
export interface CelestialState {
  timestamp: string;
  lunar_phase_name: string | null;
  lunar_illumination: string | null;
  days_to_next_new_moon: string | null;
  days_to_next_full_moon: string | null;
  is_lunar_eclipse: boolean;
  is_solar_eclipse: boolean;
  mercury_retrograde: boolean;
  venus_retrograde: boolean;
  mars_retrograde: boolean;
  jupiter_retrograde: boolean;
  saturn_retrograde: boolean;
  retrograde_count: number;
  celestial_score: string | null;
}

export interface CelestialResponse {
  date: string;
  state: CelestialState;
}

// ---------- Numerology ----------
export interface NumerologyData {
  date: string;
  date_digit_sum: number;
  is_master_number: boolean;
  master_number_value: number | null;
  universal_day_number: number;
  cycle_confluence_count: number;
  price_47_appearances: number;
  numerology_score: string | null;
}

export interface NumerologyResponse {
  date: string;
  numerology: NumerologyData;
}

// ---------- Sentiment ----------
export interface SentimentData {
  timestamp: string;
  fear_greed_index: number | null;
  fear_greed_label: string | null;
  sentiment_score: string | null;
}

export interface SentimentResponse {
  symbol: string;
  sentiment: SentimentData | null;
}

// ---------- On-Chain ----------
export interface OnchainMetrics {
  timestamp: string;
  exchange_inflow: string | null;
  exchange_outflow: string | null;
  exchange_netflow: string | null;
  whale_transactions_count: number | null;
  whale_volume_usd: string | null;
  active_addresses: number | null;
  nupl: string | null;
  mvrv_zscore: string | null;
  sopr: string | null;
  onchain_score: string | null;
}

export interface OnchainResponse {
  symbol: string;
  metrics: OnchainMetrics | null;
}

// ---------- Confluence ----------
export interface ConfluenceScores {
  ta_score: number | null;
  onchain_score: number | null;
  celestial_score: number | null;
  numerology_score: number | null;
  sentiment_score: number | null;
  political_score: number | null;
  macro_score: number | null;
}

export interface ConfluenceResponse {
  symbol: string;
  timeframe: string;
  scores: ConfluenceScores;
  composite_score: number;
  signal_strength: string;
  aligned_layers: string[];
  alignment_count: number;
  weights: Record<string, number>;
}

// ---------- Alerts ----------
export interface Alert {
  id: number;
  created_at: string | null;
  triggered_at: string | null;
  symbol: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  composite_score: string | null;
  status: string;
  acknowledged_at: string | null;
}

export interface AlertsResponse {
  count: number;
  alerts: Alert[];
}

// ---------- Political Signal ----------
export interface PoliticalSignal {
  timestamp: string;
  political_score: string | null;
  hours_to_next_major_event: number | null;
  next_event_type: string | null;
  upcoming_events_7d: number | null;
  upcoming_high_impact_7d: number | null;
  news_volume_1h: number | null;
  news_volume_24h: number | null;
  avg_news_sentiment_24h: string | null;
  dominant_narrative: string | null;
  narrative_strength: string | null;
  narrative_direction: string | null;
}

export interface PoliticalSignalResponse {
  signal: PoliticalSignal | null;
}

// ---------- Weights ----------
export interface WeightsResponse {
  profile: string;
  weights: {
    ta: number;
    onchain: number;
    celestial: number;
    numerology: number;
    sentiment: number;
    political: number;
    macro: number;
  };
}

// ---------- Macro Liquidity ----------
export interface MacroSubSignals {
  liquidity_score: string | null;
  treasury_score: string | null;
  dollar_score: string | null;
  oil_score: string | null;
  carry_trade_score: string | null;
}

export interface MacroDataPoints {
  net_liquidity: string | null;
  m2_yoy_pct: string | null;
  yield_curve_2s10s: string | null;
  dxy_value: string | null;
  vix_value: string | null;
  wti_price: string | null;
  usdjpy_value: string | null;
  carry_stress: string | null;
}

export interface MacroSignalResponse {
  timestamp: string;
  macro_score: string | null;
  regime: string | null;
  regime_confidence: string | null;
  sub_signals: MacroSubSignals;
  data_points: MacroDataPoints;
  sub_signal_detail: Record<string, unknown> | null;
  status?: string;
}

// ---------- AI Interpretation ----------
export interface InterpretationResponse {
  summary: string;
  layers: Record<string, string>;
  watch: string;
  bias: string;
  generated_at: string;
  cached: boolean;
}
