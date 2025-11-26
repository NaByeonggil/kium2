"""
잔고/포트폴리오 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from main_server.models.schemas import AccountBalance, StockHolding
from main_server.api.kiwoom_trading_client import KiwoomTradingClient
from main_server.config.settings import get_settings

router = APIRouter(prefix="/balance", tags=["잔고"])

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


@router.get("", response_model=AccountBalance)
async def get_balance(
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    계좌 잔고 조회

    Returns:
        AccountBalance: 총평가금액, 손익, 예수금, 보유종목 목록
    """
    result = client.get_balance()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "잔고 조회 실패")
        )

    holdings = [
        StockHolding(
            stock_code=h["stock_code"],
            stock_name=h["stock_name"],
            quantity=h["quantity"],
            avg_price=h["avg_price"],
            current_price=h["current_price"],
            eval_amount=h["eval_amount"],
            profit_loss=h["profit_loss"],
            profit_rate=h["profit_rate"]
        )
        for h in result.get("holdings", [])
    ]

    return AccountBalance(
        total_eval=result["total_eval"],
        total_profit_loss=result["total_profit_loss"],
        total_profit_rate=result["total_profit_rate"],
        cash_balance=result["cash_balance"],
        holdings=holdings
    )


@router.get("/summary")
async def get_balance_summary(
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    잔고 요약 정보

    Returns:
        dict: 간단한 잔고 요약
    """
    result = client.get_balance()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "잔고 조회 실패")
        )

    holdings = result.get("holdings", [])

    # 수익/손실 종목 분류
    profit_stocks = [h for h in holdings if h["profit_loss"] > 0]
    loss_stocks = [h for h in holdings if h["profit_loss"] < 0]

    return {
        "total_eval": result["total_eval"],
        "total_profit_loss": result["total_profit_loss"],
        "total_profit_rate": result["total_profit_rate"],
        "cash_balance": result["cash_balance"],
        "holdings_count": len(holdings),
        "profit_count": len(profit_stocks),
        "loss_count": len(loss_stocks),
        "invested_amount": result["total_eval"] - result["total_profit_loss"]
    }


@router.get("/holdings")
async def get_holdings(
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    보유 종목만 조회

    Returns:
        list: 보유 종목 목록
    """
    result = client.get_balance()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "잔고 조회 실패")
        )

    return result.get("holdings", [])


@router.get("/holding/{stock_code}")
async def get_holding_detail(
    stock_code: str,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    특정 종목 보유 상세

    - **stock_code**: 종목코드
    """
    result = client.get_balance()

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "잔고 조회 실패")
        )

    for holding in result.get("holdings", []):
        if holding["stock_code"] == stock_code:
            return holding

    raise HTTPException(
        status_code=404,
        detail=f"종목 {stock_code}을(를) 보유하고 있지 않습니다"
    )
