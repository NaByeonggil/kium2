"""
틱데이터 수집 엔진

WebSocket으로 실시간 틱 수신 및 DB 저장
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sub_server.api.kiwoom_client import KiwoomAPIClient
from sub_server.api.websocket_client import KiwoomWebSocket
from sub_server.services.storage_service import TickStorageService
import time
import os
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TickCollector:
    """틱데이터 수집기"""

    def __init__(self, appkey: str, secretkey: str, is_mock: bool = False):
        """
        초기화

        Args:
            appkey: 키움 App Key
            secretkey: 키움 Secret Key
            is_mock: 모의투자 여부
        """
        self.appkey = appkey
        self.secretkey = secretkey
        self.is_mock = is_mock

        # API 클라이언트 초기화
        self.api_client = KiwoomAPIClient(appkey, secretkey, is_mock)
        self.ws_client = None

        # 저장 서비스
        self.storage = TickStorageService()

        # 버퍼 설정
        self.buffer = []
        self.buffer_size = int(os.getenv('TICK_BUFFER_SIZE', 10000))
        self.buffer_lock = threading.Lock()

        # 플러시 주기 (초)
        self.flush_interval = int(os.getenv('FLUSH_INTERVAL', 10))

        # 수집 상태
        self.is_running = False
        self.tick_count = 0
        self.start_time = None

        # 수집 대상 종목
        self.stock_codes = []

    def start(self, stock_codes: list):
        """
        수집 시작

        Args:
            stock_codes: 수집할 종목코드 리스트
        """
        if self.is_running:
            logger.warning("⚠️ 이미 수집 중입니다")
            return

        self.stock_codes = stock_codes
        logger.info(f"🚀 틱데이터 수집 시작: {len(stock_codes)}개 종목")

        # 1. WebSocket 연결
        token = self.api_client.token
        self.ws_client = KiwoomWebSocket(token, self.is_mock)
        self.ws_client.connect()

        # 연결 대기
        time.sleep(2)

        if not self.ws_client.is_connected:
            logger.error("❌ WebSocket 연결 실패")
            return

        # 2. 실시간 체결 구독
        self.ws_client.subscribe_tick(stock_codes, self.on_tick_received)

        # 3. 수집 시작
        self.is_running = True
        self.start_time = datetime.now()
        self.tick_count = 0

        logger.info("✅ 틱데이터 수집 시작 완료")

        # 4. 주기적 플러시 시작
        self._start_periodic_flush()

    def on_tick_received(self, tick_data: dict):
        """
        틱 수신 콜백

        Args:
            tick_data: 틱데이터
        """
        # 버퍼에 추가
        with self.buffer_lock:
            self.buffer.append(tick_data)
            self.tick_count += 1

            # 버퍼 가득 차면 즉시 플러시
            if len(self.buffer) >= self.buffer_size:
                self._flush()

    def _flush(self):
        """버퍼 → DB 저장"""
        if not self.buffer:
            return

        try:
            # 버퍼 복사 및 초기화
            with self.buffer_lock:
                data_to_save = self.buffer.copy()
                self.buffer.clear()

            # DB 저장
            if data_to_save:
                count = self.storage.bulk_insert_ticks(data_to_save)
                logger.info(f"💾 DB 저장: {count:,}건 (총 {self.tick_count:,}건 수집)")

        except Exception as e:
            logger.error(f"❌ 플러시 실패: {e}")

    def _start_periodic_flush(self):
        """주기적 플러시 스레드 시작"""

        def flush_job():
            while self.is_running:
                time.sleep(self.flush_interval)
                if self.buffer:
                    self._flush()

        thread = threading.Thread(target=flush_job, daemon=True)
        thread.start()
        logger.info(f"⏰ 주기적 플러시 시작 ({self.flush_interval}초마다)")

    def stop(self):
        """수집 중지"""
        if not self.is_running:
            return

        logger.info("⏹️ 수집 중지 중...")

        self.is_running = False

        # 남은 버퍼 저장
        self._flush()

        # WebSocket 종료
        if self.ws_client:
            self.ws_client.close()

        # DB 연결 종료
        self.storage.close()

        # 통계 출력
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.tick_count / elapsed if elapsed > 0 else 0

            logger.info("=" * 60)
            logger.info(f"수집 통계")
            logger.info("=" * 60)
            logger.info(f"총 수집 건수: {self.tick_count:,}건")
            logger.info(f"수집 시간: {elapsed:.1f}초")
            logger.info(f"평균 수집 속도: {rate:.1f}건/초")
            logger.info("=" * 60)

        logger.info("✅ 수집 중지 완료")

    def get_stats(self) -> dict:
        """
        수집 통계 조회

        Returns:
            dict: 통계 정보
        """
        elapsed = 0
        rate = 0

        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.tick_count / elapsed if elapsed > 0 else 0

        return {
            'is_running': self.is_running,
            'tick_count': self.tick_count,
            'elapsed_seconds': elapsed,
            'ticks_per_second': rate,
            'buffer_size': len(self.buffer),
            'stock_count': len(self.stock_codes)
        }


class RankingCollector:
    """거래대금 랭킹 수집기"""

    def __init__(self, api_client: KiwoomAPIClient):
        """
        초기화

        Args:
            api_client: 키움 API 클라이언트
        """
        self.api_client = api_client
        self.storage = TickStorageService()

    def collect_top_stocks(self, limit: int = 50) -> list:
        """
        거래대금 TOP N 종목 수집

        Args:
            limit: 조회할 종목 수

        Returns:
            list: 종목 리스트
        """
        logger.info(f"📊 거래대금 TOP {limit} 종목 수집 중...")

        try:
            # 1. 전체 종목 리스트 조회 (0: 전체)
            result = self.api_client.get_stock_list("0")

            if result.get('return_code') != 0:
                logger.error(f"❌ 종목 리스트 조회 실패: {result.get('return_msg')}")
                return []

            all_stocks = result.get('data', [])

            # 2. 각 종목의 현재가 조회 (거래대금 포함)
            stock_data = []

            for stock in all_stocks[:200]:  # 일단 상위 200개만 조회
                stock_code = stock['stk_cd']

                try:
                    price_info = self.api_client.get_current_price(stock_code)

                    if price_info.get('return_code') == 0:
                        trading_value = int(price_info.get('acml_tr_pbmn', 0)) * 1000000  # 백만원 단위

                        stock_data.append({
                            'stock_code': stock_code,
                            'stock_name': price_info.get('stk_nm', ''),
                            'trading_value': trading_value,
                            'current_price': int(price_info.get('now_uv', 0)),
                            'change_rate': float(price_info.get('prdy_ctrt', 0)),
                            'volume': int(price_info.get('acml_vol', 0))
                        })

                    # Rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    logger.debug(f"종목 {stock_code} 조회 실패: {e}")
                    continue

            # 3. 거래대금 기준 정렬
            stock_data.sort(key=lambda x: x['trading_value'], reverse=True)

            # 4. TOP N 선택
            top_stocks = stock_data[:limit]

            # 5. 순위 추가
            for i, stock in enumerate(top_stocks, 1):
                stock['rank_position'] = i
                stock['collected_at'] = datetime.now()

            # 6. DB 저장
            if top_stocks:
                self.storage.insert_trading_volume_rank(top_stocks)
                logger.info(f"✅ 거래대금 TOP {len(top_stocks)}개 종목 수집 완료")

            return top_stocks

        except Exception as e:
            logger.error(f"❌ 거래대금 랭킹 수집 실패: {e}")
            return []
