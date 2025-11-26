import { useEffect, useState } from 'react';
import { orderbookApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import { formatPrice, formatVolume, calculateBarWidth } from '@/utils/format';

interface OrderbookPanelProps {
  onPriceClick?: (price: number) => void;
}

export default function OrderbookPanel({ onPriceClick }: OrderbookPanelProps) {
  const { selectedStock, orderbook, setOrderbook } = useTradingStore();
  const [isLoading, setIsLoading] = useState(false);

  // 호가 데이터 로드
  useEffect(() => {
    if (!selectedStock) {
      setOrderbook(null);
      return;
    }

    const loadOrderbook = async () => {
      setIsLoading(true);
      try {
        const data = await orderbookApi.get(selectedStock.stock_code);
        setOrderbook(data);
      } catch (error) {
        console.error('Orderbook load error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadOrderbook();

    // 1초마다 갱신
    const interval = setInterval(loadOrderbook, 1000);
    return () => clearInterval(interval);
  }, [selectedStock, setOrderbook]);

  if (!selectedStock) {
    return (
      <div className="card p-4 h-full flex items-center justify-center text-dark-muted">
        종목을 선택해주세요
      </div>
    );
  }

  if (isLoading && !orderbook) {
    return (
      <div className="card p-4 h-full flex items-center justify-center text-dark-muted">
        로딩중...
      </div>
    );
  }

  if (!orderbook) return null;

  // 최대 잔량 (바 너비 계산용)
  const maxVolume = Math.max(
    ...orderbook.asks.map((a) => a.volume),
    ...orderbook.bids.map((b) => b.volume)
  );

  // 매수/매도 비율
  const totalVolume = orderbook.total_ask_volume + orderbook.total_bid_volume;
  const bidRatio = totalVolume > 0 ? (orderbook.total_bid_volume / totalVolume) * 100 : 50;

  return (
    <div className="card p-4 h-full flex flex-col">
      {/* 헤더 */}
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <span className="font-semibold">{orderbook.stock_name}</span>
          <span className="text-2xl font-bold">{formatPrice(orderbook.current_price)}</span>
        </div>
      </div>

      {/* 컬럼 헤더 */}
      <div className="grid grid-cols-3 text-xs text-dark-muted mb-1 px-1">
        <span>매도잔량</span>
        <span className="text-center">가격</span>
        <span className="text-right">매수잔량</span>
      </div>

      {/* 호가 테이블 */}
      <div className="flex-1 overflow-hidden">
        {/* 매도 호가 (역순으로 표시) */}
        <div className="space-y-0.5">
          {[...orderbook.asks].reverse().map((ask, idx) => (
            <div
              key={`ask-${idx}`}
              className="grid grid-cols-3 items-center py-1 px-1 hover:bg-dark-border/50 cursor-pointer relative"
              onClick={() => onPriceClick?.(ask.price)}
            >
              {/* 매도잔량 바 */}
              <div className="relative">
                <div
                  className="absolute right-0 top-0 bottom-0 bg-down/20"
                  style={{ width: `${calculateBarWidth(ask.volume, maxVolume)}%` }}
                />
                <span className="relative text-sm text-down">{formatVolume(ask.volume)}</span>
              </div>
              {/* 가격 */}
              <span className="text-center text-sm font-medium text-down">
                {formatPrice(ask.price)}
              </span>
              {/* 매수잔량 (빈칸) */}
              <span />
            </div>
          ))}
        </div>

        {/* 현재가 구분선 */}
        <div className="my-2 border-t-2 border-dark-border flex items-center justify-center py-2">
          <span className="text-xl font-bold">{formatPrice(orderbook.current_price)}</span>
        </div>

        {/* 매수 호가 */}
        <div className="space-y-0.5">
          {orderbook.bids.map((bid, idx) => (
            <div
              key={`bid-${idx}`}
              className="grid grid-cols-3 items-center py-1 px-1 hover:bg-dark-border/50 cursor-pointer relative"
              onClick={() => onPriceClick?.(bid.price)}
            >
              {/* 매도잔량 (빈칸) */}
              <span />
              {/* 가격 */}
              <span className="text-center text-sm font-medium text-up">
                {formatPrice(bid.price)}
              </span>
              {/* 매수잔량 바 */}
              <div className="relative text-right">
                <div
                  className="absolute left-0 top-0 bottom-0 bg-up/20"
                  style={{ width: `${calculateBarWidth(bid.volume, maxVolume)}%` }}
                />
                <span className="relative text-sm text-up">{formatVolume(bid.volume)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 총잔량 */}
      <div className="mt-3 pt-3 border-t border-dark-border">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-down">매도 {formatVolume(orderbook.total_ask_volume)}</span>
          <span className="text-up">매수 {formatVolume(orderbook.total_bid_volume)}</span>
        </div>
        {/* 비율 바 */}
        <div className="h-2 bg-down rounded-full overflow-hidden">
          <div
            className="h-full bg-up transition-all duration-300"
            style={{ width: `${bidRatio}%` }}
          />
        </div>
        <div className="text-center text-xs text-dark-muted mt-1">
          {bidRatio > 55 ? '매수우위' : bidRatio < 45 ? '매도우위' : '중립'}
        </div>
      </div>
    </div>
  );
}
