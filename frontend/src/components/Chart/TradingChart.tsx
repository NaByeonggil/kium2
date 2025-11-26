import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import { stocksApi } from '@/services/api';
import type { CandleData, QuarterLines } from '@/types';

interface TradingChartProps {
  stockCode: string;
  stockName?: string;
  quarterLines?: QuarterLines;
  height?: number;
}

export default function TradingChart({
  stockCode,
  stockName,
  quarterLines,
  height = 400,
}: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  const [chartType, setChartType] = useState<'daily' | 'minute'>('daily');
  const [interval, setInterval] = useState(1);
  const [isLoading, setIsLoading] = useState(false);

  // 차트 초기화
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { color: '#0f0f0f' },
        textColor: '#e5e5e5',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2a2a2a',
      },
      timeScale: {
        borderColor: '#2a2a2a',
        timeVisible: true,
      },
    });

    // 캔들스틱 시리즈
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#ef4444',
      downColor: '#3b82f6',
      borderUpColor: '#ef4444',
      borderDownColor: '#3b82f6',
      wickUpColor: '#ef4444',
      wickDownColor: '#3b82f6',
    });

    // 거래량 시리즈
    const volumeSeries = chart.addHistogramSeries({
      color: '#4b5563',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;

    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height]);

  // 시간 문자열을 Unix timestamp (초)로 변환
  const parseTime = (timeStr: string, isMinute: boolean): Time => {
    if (isMinute) {
      // 분봉: "2025-11-21 15:17" -> Unix timestamp (초)
      // 한국 시간(KST, UTC+9)을 UTC timestamp로 변환
      const date = new Date(timeStr.replace(' ', 'T') + ':00+09:00');
      return Math.floor(date.getTime() / 1000) as Time;
    } else {
      // 일봉: "2025-11-21" -> 그대로 사용 (lightweight-charts 지원)
      return timeStr as Time;
    }
  };

  // 데이터 로드
  useEffect(() => {
    if (!stockCode || !candleSeriesRef.current || !volumeSeriesRef.current) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        let candles: CandleData[];
        const isMinute = chartType === 'minute';

        if (chartType === 'daily') {
          const result = await stocksApi.getDailyChart(stockCode, 120);
          candles = result.candles;
        } else {
          const result = await stocksApi.getMinuteChart(stockCode, interval);
          candles = result.candles;
        }

        if (candles && candles.length > 0) {
          // 유효한 캔들 데이터만 필터링 (null, undefined, 0 값 제외)
          const validCandles = candles.filter(
            (c) => c.open > 0 && c.high > 0 && c.low > 0 && c.close > 0 && c.time
          );

          if (validCandles.length === 0) {
            console.warn('No valid candle data');
            return;
          }

          // 캔들 데이터 변환
          const candleData: CandlestickData<Time>[] = validCandles.map((c) => ({
            time: parseTime(c.time, isMinute),
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          }));

          // 거래량 데이터
          const volumeData = validCandles.map((c) => ({
            time: parseTime(c.time, isMinute),
            value: c.volume || 0,
            color: c.close >= c.open ? 'rgba(239, 68, 68, 0.5)' : 'rgba(59, 130, 246, 0.5)',
          }));

          candleSeriesRef.current?.setData(candleData);
          volumeSeriesRef.current?.setData(volumeData);

          // 4등분 라인 그리기
          if (quarterLines && chartType === 'daily') {
            drawQuarterLines(quarterLines);
          }
        }
      } catch (error) {
        console.error('Chart data load error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [stockCode, chartType, interval, quarterLines]);

  // 4등분 라인 그리기
  const drawQuarterLines = (lines: QuarterLines) => {
    if (!candleSeriesRef.current) return;

    const pricelines = [
      { price: lines.high, color: '#ef4444', title: '고가' },
      { price: lines.q3, color: '#f97316', title: '75%' },
      { price: lines.mid, color: '#eab308', title: '50%' },
      { price: lines.q1, color: '#22c55e', title: '25%' },
      { price: lines.low, color: '#3b82f6', title: '저가' },
      { price: lines.open, color: '#a855f7', title: '시가', lineStyle: 1 },
    ];

    pricelines.forEach((line) => {
      candleSeriesRef.current?.createPriceLine({
        price: line.price,
        color: line.color,
        lineWidth: 1,
        lineStyle: line.lineStyle || 2,
        axisLabelVisible: true,
        title: line.title,
      });
    });
  };

  return (
    <div className="card p-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold">{stockName || stockCode}</span>
          {isLoading && <span className="text-dark-muted text-sm">로딩중...</span>}
        </div>

        {/* 차트 타입 선택 */}
        <div className="flex gap-2">
          <div className="flex bg-dark-bg rounded overflow-hidden">
            <button
              className={`px-3 py-1 text-sm ${chartType === 'daily' ? 'bg-dark-border text-white' : 'text-dark-muted'}`}
              onClick={() => setChartType('daily')}
            >
              일봉
            </button>
            <button
              className={`px-3 py-1 text-sm ${chartType === 'minute' ? 'bg-dark-border text-white' : 'text-dark-muted'}`}
              onClick={() => setChartType('minute')}
            >
              분봉
            </button>
          </div>

          {chartType === 'minute' && (
            <select
              value={interval}
              onChange={(e) => setInterval(Number(e.target.value))}
              className="input text-sm py-1"
            >
              <option value={1}>1분</option>
              <option value={3}>3분</option>
              <option value={5}>5분</option>
              <option value={10}>10분</option>
              <option value={30}>30분</option>
              <option value={60}>60분</option>
            </select>
          )}
        </div>
      </div>

      {/* 차트 영역 */}
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}
