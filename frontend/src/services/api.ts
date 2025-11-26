import axios from 'axios';
import type {
  StockInfo,
  StockPrice,
  Orderbook,
  OrderRequest,
  OrderResponse,
  OpenOrder,
  AccountBalance,
  CandleData,
  USETFData,
  SectorPerformance,
  StockFullInfo,
  KRETFData,
  KRSectorPerformance,
  KRSectorCategories,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
});

// 응답 인터셉터
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ========== 종목 API ==========

export const stocksApi = {
  // 종목 검색
  search: async (keyword: string, limit = 20): Promise<{ stocks: StockInfo[]; total_count: number }> => {
    const { data } = await api.get('/stocks/search', { params: { keyword, limit } });
    return data;
  },

  // 현재가 조회
  getPrice: async (stockCode: string): Promise<StockPrice> => {
    const { data } = await api.get(`/stocks/${stockCode}`);
    return data;
  },

  // 종목 종합 정보
  getFullInfo: async (stockCode: string): Promise<StockFullInfo> => {
    const { data } = await api.get(`/stocks/${stockCode}/info`);
    return data;
  },

  // 일봉 차트
  getDailyChart: async (stockCode: string, days = 60): Promise<{ candles: CandleData[] }> => {
    const { data } = await api.get(`/stocks/${stockCode}/chart/daily`, { params: { days } });
    return data;
  },

  // 분봉 차트
  getMinuteChart: async (stockCode: string, interval = 1): Promise<{ candles: CandleData[] }> => {
    const { data } = await api.get(`/stocks/${stockCode}/chart/minute`, { params: { interval } });
    return data;
  },

  // 거래대금 상위
  getTopTrading: async (market = '0', limit = 50) => {
    const { data } = await api.get('/stocks/ranking/top-trading', { params: { market, limit } });
    return data;
  },
};

// ========== 호가 API ==========

export const orderbookApi = {
  // 10호가 조회
  get: async (stockCode: string): Promise<Orderbook> => {
    const { data } = await api.get(`/orderbook/${stockCode}`);
    return data;
  },

  // 호가 요약
  getSummary: async (stockCode: string) => {
    const { data } = await api.get(`/orderbook/${stockCode}/summary`);
    return data;
  },
};

// ========== 매매 API ==========

export const tradingApi = {
  // 주문 실행
  placeOrder: async (order: OrderRequest): Promise<OrderResponse> => {
    const { data } = await api.post('/trading/order', order);
    return data;
  },

  // 매수
  buy: async (stockCode: string, quantity: number, price = 0): Promise<OrderResponse> => {
    const { data } = await api.post('/trading/buy', null, {
      params: { stock_code: stockCode, quantity, price },
    });
    return data;
  },

  // 매도
  sell: async (stockCode: string, quantity: number, price = 0): Promise<OrderResponse> => {
    const { data } = await api.post('/trading/sell', null, {
      params: { stock_code: stockCode, quantity, price },
    });
    return data;
  },

  // 정정
  modify: async (orderNo: string, stockCode: string, quantity: number, price: number) => {
    const { data } = await api.put('/trading/modify', {
      order_no: orderNo,
      stock_code: stockCode,
      quantity,
      price,
    });
    return data;
  },

  // 취소
  cancel: async (orderNo: string, stockCode: string, quantity: number) => {
    const { data } = await api.delete('/trading/cancel', {
      data: { order_no: orderNo, stock_code: stockCode, quantity },
    });
    return data;
  },

  // 미체결 조회
  getOpenOrders: async (stockCode = ''): Promise<OpenOrder[]> => {
    const { data } = await api.get('/trading/open-orders', { params: { stock_code: stockCode } });
    return data;
  },
};

// ========== 잔고 API ==========

export const balanceApi = {
  // 계좌 잔고
  get: async (): Promise<AccountBalance> => {
    const { data } = await api.get('/balance');
    return data;
  },

  // 잔고 요약
  getSummary: async () => {
    const { data } = await api.get('/balance/summary');
    return data;
  },

  // 보유 종목
  getHoldings: async () => {
    const { data } = await api.get('/balance/holdings');
    return data;
  },
};

// ========== US Market API ==========

export const usMarketApi = {
  // 모든 섹터
  getSectors: async (): Promise<USETFData[]> => {
    const { data } = await api.get('/us-market/sectors');
    return data;
  },

  // 섹터 성과
  getPerformance: async (): Promise<SectorPerformance> => {
    const { data } = await api.get('/us-market/sectors/performance');
    return data;
  },

  // 추천 섹터
  getRecommended: async () => {
    const { data } = await api.get('/us-market/sectors/recommended');
    return data;
  },

  // 단일 ETF
  getETF: async (symbol: string): Promise<USETFData> => {
    const { data } = await api.get(`/us-market/etf/${symbol}`);
    return data;
  },

  // 섹터 + 한국 종목
  getSectorWithKR: async (sectorName: string) => {
    const { data } = await api.get(`/us-market/sector/${sectorName}`);
    return data;
  },
};

// ========== KR Market API ==========

export const krMarketApi = {
  // 모든 섹터
  getSectors: async (): Promise<KRETFData[]> => {
    const { data } = await api.get('/kr-market/sectors');
    return data;
  },

  // 섹터 성과
  getPerformance: async (): Promise<KRSectorPerformance> => {
    const { data } = await api.get('/kr-market/sectors/performance');
    return data;
  },

  // 카테고리별 섹터
  getCategories: async (): Promise<KRSectorCategories> => {
    const { data } = await api.get('/kr-market/sectors/categories');
    return data;
  },

  // 단일 ETF
  getETF: async (code: string): Promise<KRETFData> => {
    const { data } = await api.get(`/kr-market/etf/${code}`);
    return data;
  },

  // ETF 목록
  getETFList: async () => {
    const { data } = await api.get('/kr-market/etf-list');
    return data;
  },
};

// ========== Sub Server API ==========

export const subServerApi = {
  // 상태
  getStatus: async () => {
    const { data } = await api.get('/sub-server/status');
    return data;
  },

  // 헬스체크
  healthCheck: async () => {
    const { data } = await api.get('/sub-server/health');
    return data;
  },

  // 수집기 통계
  getCollectorStats: async () => {
    const { data } = await api.get('/sub-server/collector');
    return data;
  },
};

export default api;
