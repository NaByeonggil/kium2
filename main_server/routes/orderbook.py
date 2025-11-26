"""
호가창 API 라우터

10호가 데이터 제공
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime

from main_server.models.schemas import Orderbook, OrderbookEntry, APIResponse
from main_server.api.kiwoom_trading_client import KiwoomTradingClient
from main_server.config.settings import get_settings

router = APIRouter(prefix="/orderbook", tags=["호가창"])

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


@router.get("/{stock_code}", response_model=Orderbook)
async def get_orderbook(
    stock_code: str,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    10호가 조회

    - **stock_code**: 종목코드 (예: 005930)

    Returns:
        Orderbook: 10호가 데이터 (매도호가 10개, 매수호가 10개)
    """
    result = client.get_orderbook(stock_code)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "호가 조회 실패")
        )

    # 응답 변환
    asks = [
        OrderbookEntry(price=a["price"], volume=a["volume"])
        for a in result["asks"]
    ]
    bids = [
        OrderbookEntry(price=b["price"], volume=b["volume"])
        for b in result["bids"]
    ]

    return Orderbook(
        stock_code=result["stock_code"],
        stock_name=result["stock_name"],
        current_price=result["current_price"],
        asks=asks,
        bids=bids,
        total_ask_volume=result["total_ask_volume"],
        total_bid_volume=result["total_bid_volume"],
        timestamp=datetime.now()
    )


@router.get("/{stock_code}/summary")
async def get_orderbook_summary(
    stock_code: str,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    호가 요약 정보

    - **stock_code**: 종목코드

    Returns:
        dict: 호가 요약 (매수/매도 우위, 스프레드 등)
    """
    result = client.get_orderbook(stock_code)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "호가 조회 실패")
        )

    total_ask = result["total_ask_volume"]
    total_bid = result["total_bid_volume"]

    # 매수/매도 비율 계산
    if total_ask + total_bid > 0:
        bid_ratio = total_bid / (total_ask + total_bid) * 100
    else:
        bid_ratio = 50.0

    # 스프레드 계산
    best_ask = result["asks"][0]["price"] if result["asks"] else 0
    best_bid = result["bids"][0]["price"] if result["bids"] else 0
    spread = best_ask - best_bid if best_ask and best_bid else 0
    spread_rate = (spread / best_bid * 100) if best_bid > 0 else 0

    return {
        "stock_code": stock_code,
        "stock_name": result["stock_name"],
        "current_price": result["current_price"],
        "best_ask": best_ask,
        "best_bid": best_bid,
        "spread": spread,
        "spread_rate": round(spread_rate, 3),
        "total_ask_volume": total_ask,
        "total_bid_volume": total_bid,
        "bid_ratio": round(bid_ratio, 2),
        "pressure": "매수우위" if bid_ratio > 55 else ("매도우위" if bid_ratio < 45 else "중립"),
        "timestamp": datetime.now().isoformat()
    }
