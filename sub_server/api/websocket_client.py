"""
키움증권 WebSocket 클라이언트

실시간 데이터 수신 (체결, 호가 등)
"""

import websocket
import json
import threading
import time
from typing import Callable, Dict
import logging

logger = logging.getLogger(__name__)


class KiwoomWebSocket:
    """키움 WebSocket 클라이언트 (재연결 로직 포함)"""

    def __init__(self, token: str, is_mock: bool = False):
        self.token = token
        base = "wss://mockapi.kiwoom.com:10000" if is_mock else "wss://api.kiwoom.com:10000"
        self.url = f"{base}/api/dostk/websocket"
        self.ws = None
        self.callbacks = {}
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.subscribed_stocks = []  # 재연결 시 재구독용

    def connect(self):
        """WebSocket 연결 (재연결 로직 포함)"""
        logger.info(f"WebSocket 연결 시도: {self.url}")

        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()

        # 연결 대기 (최대 5초)
        for _ in range(50):
            if self.is_connected:
                break
            time.sleep(0.1)

    def _on_open(self, ws):
        logger.info("✅ WebSocket 연결 성공")
        self.is_connected = True
        self.reconnect_attempts = 0

        # 재연결 시 기존 구독 복원
        if self.subscribed_stocks:
            logger.info(f"🔄 {len(self.subscribed_stocks)}개 종목 재구독 중...")
            self.subscribe_tick(self.subscribed_stocks, None)

    def _on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"⚠️ WebSocket 연결 종료: {close_msg}")
        self.is_connected = False
        self._reconnect()

    def _reconnect(self):
        """Exponential backoff 재연결"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("❌ 최대 재연결 시도 초과")
            return

        wait_time = min(60, 2 ** self.reconnect_attempts)
        logger.info(f"🔄 {wait_time}초 후 재연결 시도 ({self.reconnect_attempts + 1}/{self.max_reconnect_attempts})...")
        time.sleep(wait_time)

        self.reconnect_attempts += 1
        self.connect()

    def subscribe_tick(self, stock_codes: list, callback: Callable = None):
        """
        실시간 체결 구독 (0B)

        Args:
            stock_codes: 종목코드 리스트 (예: ["005930", "000660"])
            callback: 데이터 수신 콜백 함수
        """
        if not self.is_connected:
            logger.warning("⚠️ WebSocket 연결되지 않음")
            return

        # 콜백 등록
        if callback:
            for code in stock_codes:
                self.callbacks[f"0B:{code}"] = callback

        # 구독 목록 저장 (재연결용)
        self.subscribed_stocks = stock_codes

        # 등록 메시지 전송
        data_list = [
            {"item": f"KRX:{code}", "type": "0B"}
            for code in stock_codes
        ]

        message = {
            "header": {
                "api-id": "0B",
                "authorization": f"Bearer {self.token}",
                "cont-yn": "N",
                "next-key": ""
            },
            "body": {
                "trnm": "REG",
                "grp_no": "0001",
                "refresh": "1",
                "data": data_list
            }
        }

        self.ws.send(json.dumps(message))
        logger.info(f"📡 {len(stock_codes)}개 종목 실시간 체결 구독 완료")

    def subscribe_orderbook(self, stock_codes: list, callback: Callable = None):
        """
        실시간 호가 구독 (0D)

        Args:
            stock_codes: 종목코드 리스트
            callback: 데이터 수신 콜백 함수
        """
        if not self.is_connected:
            logger.warning("⚠️ WebSocket 연결되지 않음")
            return

        # 콜백 등록
        if callback:
            for code in stock_codes:
                self.callbacks[f"0D:{code}"] = callback

        # 등록 메시지 전송
        data_list = [
            {"item": f"KRX:{code}", "type": "0D"}
            for code in stock_codes
        ]

        message = {
            "header": {
                "api-id": "0D",
                "authorization": f"Bearer {self.token}",
                "cont-yn": "N",
                "next-key": ""
            },
            "body": {
                "trnm": "REG",
                "grp_no": "0002",
                "refresh": "1",
                "data": data_list
            }
        }

        self.ws.send(json.dumps(message))
        logger.info(f"📡 {len(stock_codes)}개 종목 실시간 호가 구독 완료")

    def unsubscribe(self, stock_codes: list, tr_type: str = "0B"):
        """
        실시간 데이터 해제

        Args:
            stock_codes: 종목코드 리스트
            tr_type: 실시간 TR 코드 (0B:체결, 0D:호가)
        """
        if not self.is_connected:
            return

        data_list = [
            {"item": f"KRX:{code}", "type": tr_type}
            for code in stock_codes
        ]

        message = {
            "header": {
                "api-id": tr_type,
                "authorization": f"Bearer {self.token}"
            },
            "body": {
                "trnm": "REMOVE",
                "grp_no": "0001",
                "data": data_list
            }
        }

        self.ws.send(json.dumps(message))
        logger.info(f"🚫 {len(stock_codes)}개 종목 구독 해제")

    def _on_message(self, ws, message):
        """실시간 데이터 수신"""
        try:
            data = json.loads(message)

            # trnm이 REAL일 때만 실시간 데이터
            if data.get('body', {}).get('trnm') == 'REAL':
                for item in data['body']['data']:
                    tr_type = item['type']
                    stock_code = item['item']
                    values = item['values']

                    # 콜백 실행
                    callback_key = f"{tr_type}:{stock_code}"
                    if callback_key in self.callbacks:
                        # 체결 데이터 파싱
                        if tr_type == "0B":
                            tick_data = {
                                'stock_code': stock_code,
                                'time': values.get('20', ''),
                                'price': int(values.get('10', 0)),
                                'volume': int(values.get('15', 0)),
                                'change_rate': float(values.get('13', 0)),
                                'high': int(values.get('19', 0)),
                                'low': int(values.get('21', 0)),
                                'open': int(values.get('18', 0)),
                                'accumulated_volume': int(values.get('16', 0))
                            }
                            self.callbacks[callback_key](tick_data)

                        # 호가 데이터 파싱
                        elif tr_type == "0D":
                            orderbook_data = {
                                'stock_code': stock_code,
                                'ask_prices': [int(values.get(str(i), 0)) for i in range(51, 61)],
                                'bid_prices': [int(values.get(str(i), 0)) for i in range(61, 71)],
                                'ask_volumes': [int(values.get(str(i), 0)) for i in range(71, 81)],
                                'bid_volumes': [int(values.get(str(i), 0)) for i in range(81, 91)]
                            }
                            self.callbacks[callback_key](orderbook_data)

        except Exception as e:
            logger.error(f"❌ 메시지 처리 오류: {e}")

    def _on_error(self, ws, error):
        logger.error(f"❌ WebSocket 에러: {error}")

    def close(self):
        """WebSocket 연결 종료"""
        if self.ws:
            self.ws.close()
        logger.info("👋 WebSocket 연결 종료")
