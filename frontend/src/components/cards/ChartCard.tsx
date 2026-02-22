import { useEffect, useRef } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from 'lightweight-charts';
import { usePrices } from '../../hooks/usePrices';
import { useSymbol } from '../../hooks/useSymbol';
import { parseScore } from '../../types/api';
import type { Timeframe } from '../../types/api';
import Card from '../ui/Card';
import Skeleton from '../ui/Skeleton';

const TIMEFRAMES: { value: Timeframe; label: string }[] = [
  { value: '1h', label: '1H' },
  { value: '4h', label: '4H' },
  { value: '1d', label: '1D' },
];

export default function ChartCard() {
  const { symbol, timeframe, setTimeframe } = useSymbol();
  const { data, isLoading } = usePrices(200);
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // Create chart on mount
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8B8D98',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: 'rgba(30, 32, 48, 0.5)' },
        horzLines: { color: 'rgba(30, 32, 48, 0.5)' },
      },
      crosshair: {
        vertLine: { color: '#D4A846', width: 1, style: 3 },
        horzLine: { color: '#D4A846', width: 1, style: 3 },
      },
      rightPriceScale: {
        borderColor: '#1E2030',
      },
      timeScale: {
        borderColor: '#1E2030',
        timeVisible: true,
      },
      handleScroll: true,
      handleScale: true,
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10B981',
      downColor: '#EF4444',
      borderUpColor: '#10B981',
      borderDownColor: '#EF4444',
      wickUpColor: '#10B981',
      wickDownColor: '#EF4444',
    });

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.85, bottom: 0 },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      volumeSeriesRef.current = null;
    };
  }, []);

  // Update data when candles change
  useEffect(() => {
    if (!data?.data || !candleSeriesRef.current || !volumeSeriesRef.current) return;

    const candles = data.data.map((c) => ({
      time: (new Date(c.timestamp).getTime() / 1000) as Time,
      open: parseScore(c.open),
      high: parseScore(c.high),
      low: parseScore(c.low),
      close: parseScore(c.close),
    }));

    const volumes = data.data.map((c) => ({
      time: (new Date(c.timestamp).getTime() / 1000) as Time,
      value: parseScore(c.volume),
      color: parseScore(c.close) >= parseScore(c.open)
        ? 'rgba(16, 185, 129, 0.3)'
        : 'rgba(239, 68, 68, 0.3)',
    }));

    candleSeriesRef.current.setData(candles);
    volumeSeriesRef.current.setData(volumes);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  const displaySymbol = symbol.replace('-', '/');

  return (
    <Card>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
          {displaySymbol} · {timeframe.toUpperCase()}
        </span>
        <div className="flex gap-1">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.value}
              onClick={() => setTimeframe(tf.value)}
              className="px-2 py-0.5 text-[10px] font-mono rounded"
              style={{
                backgroundColor: timeframe === tf.value ? 'var(--accent-gold-dim)' : 'transparent',
                color: timeframe === tf.value ? 'var(--accent-gold)' : 'var(--text-muted)',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      <div className="relative">
        <div ref={containerRef} className="h-[300px] lg:h-[400px] w-full" />
        {isLoading && (
          <Skeleton className="h-[300px] lg:h-[400px] w-full absolute inset-0" />
        )}
      </div>
    </Card>
  );
}
