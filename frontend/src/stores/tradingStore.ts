import { create } from 'zustand';
import type { StockInfo, StockPrice, Orderbook, AccountBalance, OpenOrder } from '@/types';

interface TradingState {
  // 선택된 종목
  selectedStock: StockInfo | null;
  stockPrice: StockPrice | null;
  orderbook: Orderbook | null;

  // 계좌 정보
  balance: AccountBalance | null;
  openOrders: OpenOrder[];

  // 로딩 상태
  isLoading: boolean;

  // 액션
  setSelectedStock: (stock: StockInfo | null) => void;
  setStockPrice: (price: StockPrice | null) => void;
  setOrderbook: (orderbook: Orderbook | null) => void;
  setBalance: (balance: AccountBalance | null) => void;
  setOpenOrders: (orders: OpenOrder[]) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useTradingStore = create<TradingState>((set) => ({
  selectedStock: null,
  stockPrice: null,
  orderbook: null,
  balance: null,
  openOrders: [],
  isLoading: false,

  setSelectedStock: (stock) => set({ selectedStock: stock }),
  setStockPrice: (price) => set({ stockPrice: price }),
  setOrderbook: (orderbook) => set({ orderbook }),
  setBalance: (balance) => set({ balance }),
  setOpenOrders: (orders) => set({ openOrders: orders }),
  setLoading: (loading) => set({ isLoading: loading }),
  reset: () =>
    set({
      selectedStock: null,
      stockPrice: null,
      orderbook: null,
      openOrders: [],
      isLoading: false,
    }),
}));
