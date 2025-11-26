"""
Pydantic 스키마 정의
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== Enums ==========

class OrderType(str, Enum):
    """주문 유형"""
    LIMIT = "0"      # 지정가
    MARKET = "3"     # 시장가


class OrderSide(str, Enum):
    """매매 구분"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MarketType(str, Enum):
    """시장 구분"""
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    ETF = "ETF"
    ETN = "ETN"


# ========== Stock Models ==========

class StockInfo(BaseModel):
    """종목 기본 정보"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    market_type: str = Field(..., description="시장구분")


class StockPrice(BaseModel):
    """종목 현재가 정보"""
    stock_code: str
    stock_name: str
    current_price: int = Field(..., description="현재가")
    change_price: int = Field(..., description="전일대비")
    change_rate: float = Field(..., description="등락률(%)")
    volume: int = Field(..., description="거래량")
    trading_value: int = Field(..., description="거래대금")
    high_price: int = Field(..., description="고가")
    low_price: int = Field(..., description="저가")
    open_price: int = Field(..., description="시가")
    prev_close: int = Field(..., description="전일종가")


class StockSearchResult(BaseModel):
    """종목 검색 결과"""
    stocks: List[StockInfo]
    total_count: int


# ========== Orderbook Models ==========

class OrderbookEntry(BaseModel):
    """호가 항목"""
    price: int = Field(..., description="가격")
    volume: int = Field(..., description="잔량")


class Orderbook(BaseModel):
    """10호가 데이터"""
    stock_code: str
    stock_name: str
    current_price: int
    asks: List[OrderbookEntry] = Field(..., description="매도호가 (낮은가격부터)")
    bids: List[OrderbookEntry] = Field(..., description="매수호가 (높은가격부터)")
    total_ask_volume: int = Field(..., description="총 매도잔량")
    total_bid_volume: int = Field(..., description="총 매수잔량")
    timestamp: datetime


# ========== Order Models ==========

class OrderRequest(BaseModel):
    """주문 요청"""
    stock_code: str = Field(..., description="종목코드")
    side: OrderSide = Field(..., description="매매구분")
    quantity: int = Field(..., gt=0, description="주문수량")
    price: Optional[int] = Field(None, ge=0, description="주문가격 (시장가는 0 또는 None)")
    order_type: OrderType = Field(default=OrderType.LIMIT, description="주문유형")


class OrderResponse(BaseModel):
    """주문 응답"""
    success: bool
    order_no: Optional[str] = Field(None, description="주문번호")
    message: str
    stock_code: str
    side: str
    quantity: int
    price: Optional[int]


class ModifyOrderRequest(BaseModel):
    """주문 정정 요청"""
    order_no: str = Field(..., description="원주문번호")
    stock_code: str = Field(..., description="종목코드")
    quantity: int = Field(..., gt=0, description="정정수량")
    price: int = Field(..., gt=0, description="정정가격")


class CancelOrderRequest(BaseModel):
    """주문 취소 요청"""
    order_no: str = Field(..., description="원주문번호")
    stock_code: str = Field(..., description="종목코드")
    quantity: int = Field(..., gt=0, description="취소수량")


class OpenOrder(BaseModel):
    """미체결 주문"""
    order_no: str
    stock_code: str
    stock_name: str
    side: str
    order_type: str
    order_price: int
    order_quantity: int
    filled_quantity: int
    remaining_quantity: int
    order_time: str


# ========== Balance Models ==========

class StockHolding(BaseModel):
    """보유 종목"""
    stock_code: str
    stock_name: str
    quantity: int = Field(..., description="보유수량")
    avg_price: int = Field(..., description="평균단가")
    current_price: int = Field(..., description="현재가")
    eval_amount: int = Field(..., description="평가금액")
    profit_loss: int = Field(..., description="평가손익")
    profit_rate: float = Field(..., description="수익률(%)")


class AccountBalance(BaseModel):
    """계좌 잔고"""
    total_eval: int = Field(..., description="총평가금액")
    total_profit_loss: int = Field(..., description="총평가손익")
    total_profit_rate: float = Field(..., description="총수익률(%)")
    cash_balance: int = Field(..., description="예수금")
    holdings: List[StockHolding] = Field(default=[], description="보유종목")


# ========== Chart Models ==========

class CandleData(BaseModel):
    """캔들 데이터"""
    time: str = Field(..., description="시간 (YYYY-MM-DD or YYYY-MM-DD HH:MM)")
    open: int
    high: int
    low: int
    close: int
    volume: int


class ChartResponse(BaseModel):
    """차트 응답"""
    stock_code: str
    stock_name: str
    candles: List[CandleData]
    chart_type: str = Field(..., description="차트유형 (daily, minute)")


# ========== US Market Models ==========

class USETFData(BaseModel):
    """US ETF 데이터"""
    symbol: str = Field(..., description="티커")
    name: str = Field(..., description="ETF명")
    sector: str = Field(..., description="섹터")
    price: float = Field(..., description="현재가")
    change: float = Field(..., description="변동")
    change_percent: float = Field(..., description="변동률(%)")
    prev_close: float = Field(..., description="전일종가")
    volume: int = Field(..., description="거래량")


class SectorPerformance(BaseModel):
    """섹터 성과"""
    sector_name: str
    sector_kr: str = Field(..., description="한국어 섹터명")
    etf_symbol: str
    change_percent: float
    related_kr_stocks: List[StockInfo] = Field(default=[], description="관련 한국 종목")


class USMarketSummary(BaseModel):
    """US 시장 요약"""
    updated_at: datetime
    sectors: List[SectorPerformance]
    top_gainers: List[USETFData]
    top_losers: List[USETFData]


# ========== Response Wrappers ==========

class APIResponse(BaseModel):
    """API 공통 응답"""
    success: bool
    message: str = ""
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = False
    error_code: str
    message: str
    detail: Optional[str] = None
