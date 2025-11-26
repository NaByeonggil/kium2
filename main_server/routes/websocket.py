"""
WebSocket API 라우터

실시간 데이터 스트리밍
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import asyncio
import json
import logging
from datetime import datetime

from main_server.api.kiwoom_trading_client import KiwoomTradingClient
from main_server.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 연결 관리자"""

    def __init__(self):
        # 종목별 구독자 관리
        self.stock_subscribers: Dict[str, Set[WebSocket]] = {}
        # 전체 연결 목록
        self.active_connections: Set[WebSocket] = set()
        # 트레이딩 클라이언트
        self._trading_client: Optional[KiwoomTradingClient] = None

    def get_trading_client(self) -> KiwoomTradingClient:
        """트레이딩 클라이언트 가져오기"""
        if self._trading_client is None:
            settings = get_settings()
            self._trading_client = KiwoomTradingClient(
                appkey=settings.KIWOOM_APP_KEY,
                secretkey=settings.KIWOOM_SECRET_KEY,
                is_mock=settings.KIWOOM_IS_MOCK
            )
        return self._trading_client

    async def connect(self, websocket: WebSocket):
        """새 연결 수락"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket 연결됨. 총 연결: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """연결 해제"""
        self.active_connections.discard(websocket)

        # 모든 종목 구독에서 제거
        for stock_code in list(self.stock_subscribers.keys()):
            self.stock_subscribers[stock_code].discard(websocket)
            if not self.stock_subscribers[stock_code]:
                del self.stock_subscribers[stock_code]

        logger.info(f"WebSocket 연결 해제. 총 연결: {len(self.active_connections)}")

    def subscribe(self, websocket: WebSocket, stock_code: str):
        """종목 구독"""
        if stock_code not in self.stock_subscribers:
            self.stock_subscribers[stock_code] = set()
        self.stock_subscribers[stock_code].add(websocket)
        logger.info(f"종목 {stock_code} 구독. 구독자: {len(self.stock_subscribers[stock_code])}")

    def unsubscribe(self, websocket: WebSocket, stock_code: str):
        """종목 구독 해제"""
        if stock_code in self.stock_subscribers:
            self.stock_subscribers[stock_code].discard(websocket)
            if not self.stock_subscribers[stock_code]:
                del self.stock_subscribers[stock_code]
            logger.info(f"종목 {stock_code} 구독 해제")

    async def send_to_stock_subscribers(self, stock_code: str, data: dict):
        """특정 종목 구독자들에게 데이터 전송"""
        if stock_code not in self.stock_subscribers:
            return

        disconnected = set()
        for websocket in self.stock_subscribers[stock_code]:
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.add(websocket)

        # 연결 끊긴 클라이언트 제거
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast(self, data: dict):
        """전체 브로드캐스트"""
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_json(data)
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            self.disconnect(ws)


# 전역 연결 관리자
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 엔드포인트

    메시지 형식:
    - 구독: {"action": "subscribe", "stock_code": "005930"}
    - 구독 해제: {"action": "unsubscribe", "stock_code": "005930"}
    - 핑: {"action": "ping"}

    수신 데이터:
    - 현재가: {"type": "price", "stock_code": "005930", "data": {...}}
    - 호가: {"type": "orderbook", "stock_code": "005930", "data": {...}}
    """
    await manager.connect(websocket)

    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                stock_code = data.get("stock_code")
                if stock_code:
                    manager.subscribe(websocket, stock_code)
                    await websocket.send_json({
                        "type": "subscribed",
                        "stock_code": stock_code,
                        "message": f"{stock_code} 구독 시작"
                    })

            elif action == "unsubscribe":
                stock_code = data.get("stock_code")
                if stock_code:
                    manager.unsubscribe(websocket, stock_code)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "stock_code": stock_code,
                        "message": f"{stock_code} 구독 해제"
                    })

            elif action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/price/{stock_code}")
async def websocket_price_stream(websocket: WebSocket, stock_code: str):
    """
    단일 종목 실시간 가격 스트림

    - **stock_code**: 종목코드

    1초마다 현재가 + 호가 데이터 전송
    """
    await manager.connect(websocket)
    manager.subscribe(websocket, stock_code)

    client = manager.get_trading_client()

    try:
        while True:
            # 현재가 조회
            price_data = client.get_current_price(stock_code)

            if price_data.get("success"):
                await websocket.send_json({
                    "type": "price",
                    "stock_code": stock_code,
                    "data": price_data,
                    "timestamp": datetime.now().isoformat()
                })

            # 호가 조회
            orderbook_data = client.get_orderbook(stock_code)

            if orderbook_data.get("success"):
                await websocket.send_json({
                    "type": "orderbook",
                    "stock_code": stock_code,
                    "data": orderbook_data,
                    "timestamp": datetime.now().isoformat()
                })

            await asyncio.sleep(1)  # 1초 간격

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"가격 스트림 오류 ({stock_code}): {e}")
        manager.disconnect(websocket)


@router.websocket("/ws/orderbook/{stock_code}")
async def websocket_orderbook_stream(websocket: WebSocket, stock_code: str):
    """
    단일 종목 실시간 호가 스트림

    - **stock_code**: 종목코드

    500ms마다 10호가 데이터 전송
    """
    await manager.connect(websocket)
    manager.subscribe(websocket, stock_code)

    client = manager.get_trading_client()

    try:
        while True:
            orderbook_data = client.get_orderbook(stock_code)

            if orderbook_data.get("success"):
                await websocket.send_json({
                    "type": "orderbook",
                    "stock_code": stock_code,
                    "data": orderbook_data,
                    "timestamp": datetime.now().isoformat()
                })

            await asyncio.sleep(0.5)  # 500ms 간격

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"호가 스트림 오류 ({stock_code}): {e}")
        manager.disconnect(websocket)


@router.get("/ws/connections")
async def get_websocket_stats():
    """
    WebSocket 연결 통계

    Returns:
        dict: 연결 수, 구독 현황
    """
    return {
        "total_connections": len(manager.active_connections),
        "subscriptions": {
            stock_code: len(subscribers)
            for stock_code, subscribers in manager.stock_subscribers.items()
        },
        "timestamp": datetime.now().isoformat()
    }
