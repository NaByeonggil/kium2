import { useEffect, useState } from 'react';
import { tradingApi } from '@/services/api';
import { useTradingStore } from '@/stores/tradingStore';
import { formatPrice } from '@/utils/format';
import { X, Edit2 } from 'lucide-react';

export default function OpenOrdersPanel() {
  const { openOrders, setOpenOrders } = useTradingStore();
  const [isLoading, setIsLoading] = useState(false);

  // 미체결 주문 로드
  useEffect(() => {
    const loadOrders = async () => {
      setIsLoading(true);
      try {
        const orders = await tradingApi.getOpenOrders();
        setOpenOrders(orders);
      } catch (error) {
        console.error('Open orders load error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadOrders();
    const interval = setInterval(loadOrders, 5000);
    return () => clearInterval(interval);
  }, [setOpenOrders]);

  // 주문 취소
  const handleCancel = async (orderNo: string, stockCode: string, quantity: number) => {
    if (!confirm('주문을 취소하시겠습니까?')) return;

    try {
      const result = await tradingApi.cancel(orderNo, stockCode, quantity);
      if (result.success) {
        const orders = await tradingApi.getOpenOrders();
        setOpenOrders(orders);
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert('주문 취소 실패');
    }
  };

  if (isLoading && openOrders.length === 0) {
    return (
      <div className="card p-4">
        <div className="text-dark-muted">로딩중...</div>
      </div>
    );
  }

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold">미체결 주문</span>
        <span className="text-sm text-dark-muted">{openOrders.length}건</span>
      </div>

      {openOrders.length === 0 ? (
        <div className="text-center text-dark-muted py-4">미체결 주문이 없습니다</div>
      ) : (
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {openOrders.map((order) => (
            <div
              key={order.order_no}
              className="p-3 bg-dark-bg rounded flex items-center justify-between"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      order.side === 'buy' ? 'bg-up/20 text-up' : 'bg-down/20 text-down'
                    }`}
                  >
                    {order.side === 'buy' ? '매수' : '매도'}
                  </span>
                  <span className="font-medium">{order.stock_name}</span>
                </div>
                <div className="text-sm text-dark-muted mt-1">
                  {formatPrice(order.order_price)}원 × {order.remaining_quantity}주
                </div>
              </div>
              <div className="flex gap-1">
                <button
                  className="p-2 hover:bg-dark-border rounded transition-colors"
                  title="정정"
                >
                  <Edit2 className="w-4 h-4 text-dark-muted" />
                </button>
                <button
                  className="p-2 hover:bg-dark-border rounded transition-colors"
                  title="취소"
                  onClick={() => handleCancel(order.order_no, order.stock_code, order.remaining_quantity)}
                >
                  <X className="w-4 h-4 text-dark-muted" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
