// 종목 정보
export interface StockInfo {
  stock_code: string;
  stock_name: string;
  market_type: string;
}

// 현재가
export interface StockPrice {
  stock_code: string;
  stock_name: string;
  current_price: number;
  change_price: number;
  change_rate: number;
  volume: number;
  trading_value: number;
  high_price: number;
  low_price: number;
  open_price: number;
  prev_close: number;
}

// 호가 항목
export interface OrderbookEntry {
  price: number;
  volume: number;
}

// 호가창
export interface Orderbook {
  stock_code: string;
  stock_name: string;
  current_price: number;
  asks: OrderbookEntry[];
  bids: OrderbookEntry[];
  total_ask_volume: number;
  total_bid_volume: number;
  timestamp: string;
}

// 주문 요청
export interface OrderRequest {
  stock_code: string;
  side: 'buy' | 'sell';
  quantity: number;
  price?: number;
  order_type: '0' | '3'; // 0: 지정가, 3: 시장가
}

// 주문 응답
export interface OrderResponse {
  success: boolean;
  order_no?: string;
  message: string;
  stock_code: string;
  side: string;
  quantity: number;
  price?: number;
}

// 미체결 주문
export interface OpenOrder {
  order_no: string;
  stock_code: string;
  stock_name: string;
  side: string;
  order_type: string;
  order_price: number;
  order_quantity: number;
  filled_quantity: number;
  remaining_quantity: number;
  order_time: string;
}

// 보유 종목
export interface StockHolding {
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  eval_amount: number;
  profit_loss: number;
  profit_rate: number;
}

// 계좌 잔고
export interface AccountBalance {
  total_eval: number;
  total_profit_loss: number;
  total_profit_rate: number;
  cash_balance: number;
  holdings: StockHolding[];
}

// 캔들 데이터
export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// US ETF 데이터
export interface USETFData {
  symbol: string;
  name: string;
  sector: string;
  sector_kr: string;
  price: number;
  prev_close: number;
  change: number;
  change_percent: number;
  volume: number;
  related_kr_stocks?: StockInfo[];
}

// 섹터 성과
export interface SectorPerformance {
  updated_at: string;
  top_gainers: USETFData[];
  top_losers: USETFData[];
  all_sectors: USETFData[];
}

// 4등분 라인
export interface QuarterLines {
  high: number;
  q3: number;
  mid: number;
  q1: number;
  low: number;
  open: number;
}

// 종목 종합 정보
export interface StockFullInfo {
  stock_code: string;
  stock_name: string;
  market_type: string;
  price: StockPrice;
  quarter_lines: QuarterLines;
  orderbook?: {
    asks: OrderbookEntry[];
    bids: OrderbookEntry[];
    total_ask: number;
    total_bid: number;
  };
  timestamp: string;
}

// KR ETF 데이터
export interface KRETFData {
  code: string;
  name: string;
  sector: string;
  sector_kr: string;
  price: number;
  prev_close: number;
  change: number;
  change_percent: number;
  volume: number;
  is_loading?: boolean;
  related_stocks?: { code: string; name: string }[];
}

// KR 섹터 성과
export interface KRSectorPerformance {
  updated_at: string;
  top_gainers: KRETFData[];
  top_losers: KRETFData[];
  all_sectors: KRETFData[];
}

// KR 섹터 카테고리
export interface KRSectorCategory {
  name: string;
  etfs: KRETFData[];
}

export interface KRSectorCategories {
  updated_at: string;
  categories: {
    [key: string]: KRSectorCategory;
  };
}
