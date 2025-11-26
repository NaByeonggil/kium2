"""
매매 API 라우터

매수/매도/정정/취소 주문 처리
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List

from main_server.models.schemas import (
    OrderRequest, OrderResponse, ModifyOrderRequest,
    CancelOrderRequest, OpenOrder, APIResponse
)
from main_server.api.kiwoom_trading_client import KiwoomTradingClient
from main_server.config.settings import get_settings

router = APIRouter(prefix="/trading", tags=["매매"])

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


@router.post("/order", response_model=OrderResponse)
async def place_order(
    order: OrderRequest,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    주문 실행 (매수/매도)

    - **stock_code**: 종목코드
    - **side**: 매매구분 (buy/sell)
    - **quantity**: 주문수량
    - **price**: 주문가격 (시장가는 0 또는 생략)
    - **order_type**: 주문유형 (0:지정가, 3:시장가)
    """
    try:
        # 주문 유형 결정
        price = order.price or 0
        order_type = order.order_type.value

        if order.side.value == "buy":
            result = client.buy(
                stock_code=order.stock_code,
                quantity=order.quantity,
                price=price,
                order_type=order_type
            )
        else:
            result = client.sell(
                stock_code=order.stock_code,
                quantity=order.quantity,
                price=price,
                order_type=order_type
            )

        return OrderResponse(
            success=result["success"],
            order_no=result.get("order_no"),
            message=result["message"],
            stock_code=order.stock_code,
            side=order.side.value,
            quantity=order.quantity,
            price=price if price > 0 else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/buy", response_model=OrderResponse)
async def buy_stock(
    stock_code: str,
    quantity: int,
    price: int = 0,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    매수 주문 (간편)

    - **stock_code**: 종목코드
    - **quantity**: 주문수량
    - **price**: 주문가격 (0이면 시장가)
    """
    result = client.buy(stock_code, quantity, price)

    return OrderResponse(
        success=result["success"],
        order_no=result.get("order_no"),
        message=result["message"],
        stock_code=stock_code,
        side="buy",
        quantity=quantity,
        price=price if price > 0 else None
    )


@router.post("/sell", response_model=OrderResponse)
async def sell_stock(
    stock_code: str,
    quantity: int,
    price: int = 0,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    매도 주문 (간편)

    - **stock_code**: 종목코드
    - **quantity**: 주문수량
    - **price**: 주문가격 (0이면 시장가)
    """
    result = client.sell(stock_code, quantity, price)

    return OrderResponse(
        success=result["success"],
        order_no=result.get("order_no"),
        message=result["message"],
        stock_code=stock_code,
        side="sell",
        quantity=quantity,
        price=price if price > 0 else None
    )


@router.put("/modify", response_model=APIResponse)
async def modify_order(
    request: ModifyOrderRequest,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    주문 정정

    - **order_no**: 원주문번호
    - **stock_code**: 종목코드
    - **quantity**: 정정수량
    - **price**: 정정가격
    """
    result = client.modify_order(
        order_no=request.order_no,
        stock_code=request.stock_code,
        quantity=request.quantity,
        price=request.price
    )

    return APIResponse(
        success=result["success"],
        message=result["message"],
        data={"order_no": result.get("order_no")} if result.get("order_no") else None
    )


@router.delete("/cancel", response_model=APIResponse)
async def cancel_order(
    request: CancelOrderRequest,
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    주문 취소

    - **order_no**: 원주문번호
    - **stock_code**: 종목코드
    - **quantity**: 취소수량
    """
    result = client.cancel_order(
        order_no=request.order_no,
        stock_code=request.stock_code,
        quantity=request.quantity
    )

    return APIResponse(
        success=result["success"],
        message=result["message"]
    )


@router.get("/open-orders", response_model=List[OpenOrder])
async def get_open_orders(
    stock_code: str = "",
    client: KiwoomTradingClient = Depends(get_trading_client)
):
    """
    미체결 주문 조회

    - **stock_code**: 종목코드 (빈값이면 전체)
    """
    result = client.get_open_orders(stock_code)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "미체결 조회 실패")
        )

    return [
        OpenOrder(
            order_no=o["order_no"],
            stock_code=o["stock_code"],
            stock_name=o["stock_name"],
            side=o["side"],
            order_type=o["order_type"],
            order_price=o["order_price"],
            order_quantity=o["order_quantity"],
            filled_quantity=o["filled_quantity"],
            remaining_quantity=o["remaining_quantity"],
            order_time=o["order_time"]
        )
        for o in result.get("orders", [])
    ]
