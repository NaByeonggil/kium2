import { useEffect } from 'react';
import Header from '@/components/Layout/Header';
import TradingChart from '@/components/Chart/TradingChart';
import OrderbookPanel from '@/components/Orderbook/OrderbookPanel';
import TradingPanel from '@/components/Trading/TradingPanel';
import OpenOrdersPanel from '@/components/Trading/OpenOrdersPanel';
import BalancePanel from '@/components/Balance/BalancePanel';
import USSectorPanel from '@/components/USMarket/USSectorPanel';
import KRSectorPanel from '@/components/KRMarket/KRSectorPanel';
import { useTradingStore } from '@/stores/tradingStore';
import { wsService } from '@/services/websocket';
import type { Orderbook, StockPrice } from '@/types';

export default function App() {
  const { selectedStock, setStockPrice, setOrderbook } = useTradingStore();

  // WebSocket 연결 및 이벤트 핸들러
  useEffect(() => {
    wsService.connect();

    // 실시간 호가 업데이트
    wsService.on('orderbook', (data: Orderbook) => {
      if (data.stock_code === selectedStock?.stock_code) {
        setOrderbook(data);
      }
    });

    // 실시간 체결가 업데이트
    wsService.on('price', (data: StockPrice) => {
      if (data.stock_code === selectedStock?.stock_code) {
        setStockPrice(data);
      }
    });

    return () => {
      wsService.disconnect();
    };
  }, [selectedStock?.stock_code, setStockPrice, setOrderbook]);

  // 종목 변경 시 WebSocket 구독
  useEffect(() => {
    if (selectedStock?.stock_code) {
      wsService.subscribe(selectedStock.stock_code);
    }
  }, [selectedStock?.stock_code]);

  return (
    <div className="min-h-screen bg-dark-bg text-dark-text flex flex-col">
      {/* 헤더 */}
      <Header />

      {/* 메인 컨텐츠 */}
      <main className="flex-1 p-4 overflow-hidden">
        <div className="h-full grid grid-cols-12 gap-4">
          {/* 좌측: KR + US 섹터 */}
          <div className="col-span-4 flex flex-col gap-4 overflow-hidden">
            <div className="flex-1 overflow-hidden">
              <KRSectorPanel />
            </div>
            <div className="flex-1 overflow-hidden">
              <USSectorPanel />
            </div>
          </div>

          {/* 중앙: 차트 + 잔고 + 미체결 */}
          <div className="col-span-5 flex flex-col gap-4 overflow-hidden">
            <div className="flex-[2] min-h-0">
              <TradingChart
                stockCode={selectedStock?.stock_code || ''}
                stockName={selectedStock?.stock_name}
              />
            </div>
            <div className="flex-1 min-h-0 grid grid-cols-2 gap-4">
              <BalancePanel />
              <OpenOrdersPanel />
            </div>
          </div>

          {/* 우측: 호가창 + 주문패널 */}
          <div className="col-span-3 flex flex-col gap-4 overflow-hidden">
            <div className="flex-1 overflow-hidden">
              <OrderbookPanel />
            </div>
            <div className="h-auto">
              <TradingPanel />
            </div>
          </div>
        </div>
      </main>

      {/* 푸터: 선택된 종목 정보 */}
      {selectedStock && (
        <footer className="h-10 bg-dark-card border-t border-dark-border px-4 flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <span className="text-dark-muted">선택 종목:</span>
            <span className="font-medium">{selectedStock.stock_name}</span>
            <span className="text-dark-muted">({selectedStock.stock_code})</span>
          </div>
          <div className="text-dark-muted">
            © 2024 GSLTS Trading Dashboard
          </div>
        </footer>
      )}
    </div>
  );
}
