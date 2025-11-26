"""
종목 API 라우터

종목 검색, 현재가, 차트 데이터
- 키움 API 검색 → DB 자동 등록 기능 포함
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from main_server.models.schemas import (
    StockInfo, StockPrice, StockSearchResult, ChartResponse, CandleData
)
from main_server.api.kiwoom_trading_client import KiwoomTradingClient
from main_server.services.stock_service import get_stock_service
from main_server.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["종목"])

# 클라이언트 싱글톤
_trading_client: Optional[KiwoomTradingClient] = None


def get_trading_client() -> KiwoomTradingClient:
    """트레이딩 클라이언트 의존성"""
    global _trading_client
    if _trading_client is None:
        settings = get_settings()
        _trading_client = KiwoomTradingClient(
            appkey=settings.KIWOOM_APP_KEY,
            secretkey=settings.KIWOOM_SECRET_KEY,
            is_mock=settings.KIWOOM_IS_MOCK
        )
    return _trading_client


@router.get("/search", response_model=StockSearchResult)
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="검색어 (종목명 또는 종목코드)"),
    limit: int = Query(20, ge=1, le=100, description="최대 결과 수"),
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    종목 검색 (키움 API + DB 연동)

    - **keyword**: 검색어 (종목명 또는 종목코드)
    - **limit**: 최대 결과 수 (기본 20)

    1. 캐시된 종목 목록에서 검색
    2. 종목코드 직접 입력 시 키움 API로 조회 → DB 자동 등록

    Examples:
        - 삼성 → 삼성전자, 삼성SDI, 삼성바이오로직스...
        - 005930 → 삼성전자
        - 060250 → NHN KCP (DB에 없어도 키움 API로 조회 후 등록)
    """
    results = client.search_stocks(keyword, limit)

    # 종목코드 직접 입력인데 결과가 없으면 키움 API로 직접 조회
    if not results and keyword.isdigit() and len(keyword) == 6:
        logger.info(f"🔍 종목코드 직접 조회 시도: {keyword}")
        price_result = client.get_current_price(keyword)

        if price_result.get("success") and price_result.get("stock_name"):
            stock_name = price_result["stock_name"]
            market_type = client.get_market_type(keyword)

            # DB에 등록
            stock_service = get_stock_service()
            stock_service.register_stock(keyword, stock_name, market_type)

            results = [{
                "stock_code": keyword,
                "stock_name": stock_name,
                "market_type": market_type
            }]
            logger.info(f"✅ 신규 종목 등록: {keyword} - {stock_name}")

    stocks = [
        StockInfo(
            stock_code=s["stock_code"],
            stock_name=s["stock_name"],
            market_type=s["market_type"]
        )
        for s in results
    ]

    return StockSearchResult(
        stocks=stocks,
        total_count=len(stocks)
    )


@router.get("/{stock_code}", response_model=StockPrice)
async def get_stock_price(
    stock_code: str,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    종목 현재가 조회

    - **stock_code**: 종목코드 (예: 005930)
    """
    result = client.get_current_price(stock_code)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "현재가 조회 실패")
        )

    return StockPrice(
        stock_code=result["stock_code"],
        stock_name=result["stock_name"],
        current_price=result["current_price"],
        change_price=result["change_price"],
        change_rate=result["change_rate"],
        volume=result["volume"],
        trading_value=result["trading_value"],
        high_price=result["high_price"],
        low_price=result["low_price"],
        open_price=result["open_price"],
        prev_close=result["prev_close"]
    )


@router.get("/{stock_code}/chart/daily", response_model=ChartResponse)
async def get_daily_chart(
    stock_code: str,
    days: int = Query(60, ge=1, le=365, description="조회 일수"),
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    일봉 차트 조회

    - **stock_code**: 종목코드
    - **days**: 조회 일수 (기본 60일)
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    result = client.get_daily_chart(stock_code, start_date, end_date)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "차트 조회 실패")
        )

    # 날짜 포맷 변환
    candles = []
    for c in result.get("candles", []):
        time_str = c["time"]
        if len(time_str) == 8:
            time_str = f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]}"

        candles.append(CandleData(
            time=time_str,
            open=c["open"],
            high=c["high"],
            low=c["low"],
            close=c["close"],
            volume=c["volume"]
        ))

    # 종목명 조회
    price_result = client.get_current_price(stock_code)
    stock_name = price_result.get("stock_name", stock_code) if price_result.get("success") else stock_code

    return ChartResponse(
        stock_code=stock_code,
        stock_name=stock_name,
        candles=candles,
        chart_type="daily"
    )


@router.get("/{stock_code}/chart/minute", response_model=ChartResponse)
async def get_minute_chart(
    stock_code: str,
    interval: int = Query(1, description="분봉 간격 (1, 3, 5, 10, 30, 60)"),
    date: Optional[str] = Query(None, description="조회일 (YYYYMMDD, 기본 오늘)"),
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    분봉 차트 조회

    - **stock_code**: 종목코드
    - **interval**: 분봉 간격 (1, 3, 5, 10, 30, 60분)
    - **date**: 조회일 (기본 오늘)
    """
    valid_intervals = [1, 3, 5, 10, 30, 60]
    if interval not in valid_intervals:
        raise HTTPException(
            status_code=400,
            detail=f"interval은 {valid_intervals} 중 하나여야 합니다"
        )

    if date is None:
        date = datetime.now().strftime("%Y%m%d")

    result = client.get_minute_chart(stock_code, date, str(interval))

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "차트 조회 실패")
        )

    candles = [
        CandleData(
            time=c["time"],
            open=c["open"],
            high=c["high"],
            low=c["low"],
            close=c["close"],
            volume=c["volume"]
        )
        for c in result.get("candles", [])
    ]

    # 종목명 조회
    price_result = client.get_current_price(stock_code)
    stock_name = price_result.get("stock_name", stock_code) if price_result.get("success") else stock_code

    return ChartResponse(
        stock_code=stock_code,
        stock_name=stock_name,
        candles=candles,
        chart_type=f"minute_{interval}"
    )


@router.get("/ranking/top-trading")
async def get_top_trading_stocks(
    market: str = Query("0", description="시장구분 (0:전체, 1:코스피, 2:코스닥)"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    거래대금 상위 종목

    - **market**: 시장구분 (0:전체, 1:코스피, 2:코스닥)
    - **limit**: 조회 개수 (기본 50)
    """
    results = client.get_top_trading_value(market, limit)

    return {
        "updated_at": datetime.now().isoformat(),
        "market": market,
        "stocks": results
    }


@router.get("/{stock_code}/info")
async def get_stock_full_info(
    stock_code: str,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    종목 종합 정보 (현재가 + 호가 + 4등분 라인)

    - **stock_code**: 종목코드
    """
    # 현재가 조회
    price_result = client.get_current_price(stock_code)

    if not price_result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=price_result.get("error", "종목 조회 실패")
        )

    # 호가 조회
    orderbook_result = client.get_orderbook(stock_code)

    # 4등분 라인 계산
    high = price_result["high_price"]
    low = price_result["low_price"]
    price_range = high - low

    quarter_lines = {
        "high": high,
        "q3": low + int(price_range * 0.75),
        "mid": low + int(price_range * 0.50),
        "q1": low + int(price_range * 0.25),
        "low": low,
        "open": price_result["open_price"]
    }

    return {
        "stock_code": stock_code,
        "stock_name": price_result["stock_name"],
        "market_type": client.get_market_type(stock_code),
        "price": {
            "current": price_result["current_price"],
            "change": price_result["change_price"],
            "change_rate": price_result["change_rate"],
            "high": price_result["high_price"],
            "low": price_result["low_price"],
            "open": price_result["open_price"],
            "prev_close": price_result["prev_close"],
            "volume": price_result["volume"],
            "trading_value": price_result["trading_value"]
        },
        "quarter_lines": quarter_lines,
        "orderbook": {
            "asks": orderbook_result.get("asks", [])[:5],
            "bids": orderbook_result.get("bids", [])[:5],
            "total_ask": orderbook_result.get("total_ask_volume", 0),
            "total_bid": orderbook_result.get("total_bid_volume", 0)
        } if orderbook_result.get("success") else None,
        "timestamp": datetime.now().isoformat()
    }
