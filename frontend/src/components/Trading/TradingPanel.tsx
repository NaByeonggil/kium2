import { useState, useEffect } from 'react';
import { tradingApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import { formatPrice } from '@/utils/format';

type OrderSide = 'buy' | 'sell';
type OrderType = 'limit' | 'market';

interface TradingPanelProps {
  initialPrice?: number;
}

export default function TradingPanel({ initialPrice }: TradingPanelProps) {
  const { selectedStock, stockPrice, balance } = useTradingStore();

  const [side, setSide] = useState<OrderSide>('buy');
  const [orderType, setOrderType] = useState<OrderType>('limit');
  const [price, setPrice] = useState<string>('');
  const [quantity, setQuantity] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 가격 초기화
  useEffect(() => {
    if (initialPrice) {
      setPrice(initialPrice.toString());
    } else if (stockPrice?.current_price) {
      setPrice(stockPrice.current_price.toString());
    }
  }, [initialPrice, stockPrice?.current_price]);

  // 주문 제출
  const handleSubmit = async () => {
    if (!selectedStock || !quantity) {
      setMessage({ type: 'error', text: '수량을 입력해주세요' });
      return;
    }

    if (orderType === 'limit' && !price) {
      setMessage({ type: 'error', text: '가격을 입력해주세요' });
      return;
    }

    setIsSubmitting(true);
    setMessage(null);

    try {
      const orderPrice = orderType === 'market' ? 0 : Number(price);

      let result;
      if (side === 'buy') {
        result = await tradingApi.buy(selectedStock.stock_code, Number(quantity), orderPrice);
      } else {
        result = await tradingApi.sell(selectedStock.stock_code, Number(quantity), orderPrice);
      }

      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        setQuantity('');
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '주문 처리 중 오류가 발생했습니다' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // 총 주문금액 계산
  const totalAmount = Number(price || 0) * Number(quantity || 0);

  // 비율 버튼으로 수량 설정
  const setQuantityByRatio = (ratio: number) => {
    if (!balance || !price) return;

    if (side === 'buy') {
      // 매수: 예수금 기준
      const maxQty = Math.floor(balance.cash_balance / Number(price));
      setQuantity(Math.floor(maxQty * ratio).toString());
    } else {
      // 매도: 보유수량 기준
      const holding = balance.holdings.find((h) => h.stock_code === selectedStock?.stock_code);
      if (holding) {
        setQuantity(Math.floor(holding.quantity * ratio).toString());
      }
    }
  };

  if (!selectedStock) {
    return (
      <div className="card p-4 h-full flex items-center justify-center text-dark-muted">
        종목을 선택해주세요
      </div>
    );
  }

  return (
    <div className="card p-4 h-full flex flex-col">
      {/* 매수/매도 탭 */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <button
          className={`py-3 rounded font-bold text-lg transition-colors ${
            side === 'buy' ? 'bg-up text-white' : 'bg-dark-border text-dark-muted'
          }`}
          onClick={() => setSide('buy')}
        >
          매수
        </button>
        <button
          className={`py-3 rounded font-bold text-lg transition-colors ${
            side === 'sell' ? 'bg-down text-white' : 'bg-dark-border text-dark-muted'
          }`}
          onClick={() => setSide('sell')}
        >
          매도
        </button>
      </div>

      {/* 주문 유형 */}
      <div className="flex gap-2 mb-4">
        <button
          className={`flex-1 py-2 rounded text-sm ${
            orderType === 'limit' ? 'bg-dark-border text-white' : 'bg-dark-bg text-dark-muted'
          }`}
          onClick={() => setOrderType('limit')}
        >
          지정가
        </button>
        <button
          className={`flex-1 py-2 rounded text-sm ${
            orderType === 'market' ? 'bg-dark-border text-white' : 'bg-dark-bg text-dark-muted'
          }`}
          onClick={() => setOrderType('market')}
        >
          시장가
        </button>
      </div>

      {/* 가격 입력 */}
      {orderType === 'limit' && (
        <div className="mb-4">
          <label className="block text-sm text-dark-muted mb-1">가격</label>
          <div className="flex gap-2">
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="input flex-1 text-right"
              placeholder="0"
            />
            <span className="flex items-center text-dark-muted">원</span>
          </div>
          {/* 호가 단위 버튼 */}
          <div className="flex gap-1 mt-2">
            {[-500, -100, +100, +500].map((delta) => (
              <button
                key={delta}
                className="flex-1 py-1 text-xs bg-dark-bg rounded hover:bg-dark-border"
                onClick={() => setPrice((Number(price) + delta).toString())}
              >
                {delta > 0 ? '+' : ''}{delta}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 수량 입력 */}
      <div className="mb-4">
        <label className="block text-sm text-dark-muted mb-1">수량</label>
        <div className="flex gap-2">
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className="input flex-1 text-right"
            placeholder="0"
          />
          <span className="flex items-center text-dark-muted">주</span>
        </div>
        {/* 비율 버튼 */}
        <div className="flex gap-1 mt-2">
          {[0.1, 0.25, 0.5, 1].map((ratio) => (
            <button
              key={ratio}
              className="flex-1 py-1 text-xs bg-dark-bg rounded hover:bg-dark-border"
              onClick={() => setQuantityByRatio(ratio)}
            >
              {ratio * 100}%
            </button>
          ))}
        </div>
      </div>

      {/* 주문 금액 */}
      <div className="mb-4 p-3 bg-dark-bg rounded">
        <div className="flex justify-between text-sm">
          <span className="text-dark-muted">총 주문금액</span>
          <span className="font-bold">{formatPrice(totalAmount)}원</span>
        </div>
      </div>

      {/* 메시지 */}
      {message && (
        <div
          className={`mb-4 p-3 rounded text-sm ${
            message.type === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* 주문 버튼 */}
      <button
        className={`w-full py-4 rounded font-bold text-lg transition-colors ${
          side === 'buy'
            ? 'bg-up hover:bg-up-dark text-white'
            : 'bg-down hover:bg-down-dark text-white'
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        onClick={handleSubmit}
        disabled={isSubmitting || !quantity}
      >
        {isSubmitting ? '처리중...' : side === 'buy' ? '매수' : '매도'}
      </button>
    </div>
  );
}
