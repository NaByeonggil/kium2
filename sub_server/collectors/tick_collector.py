"""
틱데이터 수집 엔진

WebSocket으로 실시간 틱 수신 및 DB 저장
WebSocket 실패 시 REST API 폴링으로 자동 전환
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
    """틱데이터 수집기 (WebSocket + REST API 폴링 하이브리드)"""

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

        # Redis 서비스 (선택적)
        self.redis = None
        try:
            from sub_server.services.redis_service import RedisService
            self.redis = RedisService()
            if not self.redis.is_connected():
                logger.warning("⚠️ Redis 연결 실패, 커스텀 종목 영구 저장 비활성화")
                self.redis = None
        except Exception as e:
            logger.warning(f"⚠️ Redis 서비스 초기화 실패: {e}")
            self.redis = None

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
        self.stock_info = {}  # {stock_code: stock_name} 형태로 저장

        # 수집 모드 및 폴링 설정
        self.collection_mode = 'websocket'  # 'websocket' 또는 'polling'
        self.polling_interval = int(os.getenv('POLLING_INTERVAL', 2))  # 기본 2초
        self.websocket_timeout = 15  # WebSocket 데이터 수신 대기 시간 (초) - 빠른 폴링 전환
        self.websocket_failure_count = 0  # WebSocket 실패 카운트
        self.max_websocket_failures = 3  # 최대 실패 허용 횟수
        self.last_tick_time = None
        self.polling_thread = None

    def start(self, stock_codes: list, stock_info: dict = None):
        """
        수집 시작

        Args:
            stock_codes: 수집할 종목코드 리스트
            stock_info: 종목 정보 딕셔너리 {stock_code: stock_name} (선택)
        """
        if self.is_running:
            logger.warning("⚠️ 이미 수집 중입니다")
            return

        self.stock_codes = stock_codes
        self.stock_info = stock_info or {}
        logger.info(f"🚀 틱데이터 수집 시작: {len(stock_codes)}개 종목")

        # 1. WebSocket 연결 시도
        token = self.api_client.token
        self.ws_client = KiwoomWebSocket(token, self.is_mock)
        self.ws_client.connect()

        # 연결 대기
        time.sleep(2)

        if not self.ws_client.is_connected:
            logger.error("❌ WebSocket 연결 실패 → REST API 폴링 모드로 전환")
            self._start_polling_mode()
            return

        # 2. 실시간 체결 구독
        self.ws_client.subscribe_tick(stock_codes, self.on_tick_received)

        # 3. 수집 시작
        self.is_running = True
        self.collection_mode = 'websocket'
        self.start_time = datetime.now()
        self.tick_count = 0
        self.last_tick_time = datetime.now()

        logger.info("✅ WebSocket 모드로 틱데이터 수집 시작")

        # 4. 주기적 플러시 시작
        self._start_periodic_flush()

        # 5. WebSocket 타임아웃 모니터링 시작
        self._start_websocket_monitor()

    def _start_websocket_monitor(self):
        """WebSocket 데이터 수신 모니터링 (타임아웃 시 폴링 전환)"""

        def monitor_job():
            while self.is_running and self.collection_mode == 'websocket':
                time.sleep(10)  # 10초마다 체크

                # WebSocket 연결 실패 횟수 체크
                if self.websocket_failure_count >= self.max_websocket_failures:
                    logger.warning(f"⚠️ WebSocket 연결 {self.websocket_failure_count}회 실패 → REST API 폴링으로 전환")
                    self._switch_to_polling_mode()
                    break

                # 데이터 수신 타임아웃 체크
                if self.last_tick_time:
                    elapsed = (datetime.now() - self.last_tick_time).total_seconds()

                    # WebSocket에서 30초 이상 데이터 없으면 폴링 전환
                    if elapsed > self.websocket_timeout:
                        logger.warning(f"⚠️ WebSocket 데이터 {elapsed:.0f}초간 없음 → REST API 폴링으로 전환")
                        self._switch_to_polling_mode()
                        break

        thread = threading.Thread(target=monitor_job, daemon=True)
        thread.start()

    def _start_polling_mode(self):
        """REST API 폴링 모드 시작"""
        logger.info("📡 REST API 폴링 모드 시작")

        self.is_running = True
        self.collection_mode = 'polling'
        self.start_time = datetime.now()
        self.tick_count = 0

        # 주기적 플러시 시작
        self._start_periodic_flush()

        # 폴링 스레드 시작
        def polling_job():
            logger.info(f"⏰ {self.polling_interval}초 간격으로 폴링 시작")

            while self.is_running and self.collection_mode == 'polling':
                try:
                    # 각 종목에 대해 현재가 조회 (ka10001)
                    for stock_code in self.stock_codes:
                        if not self.is_running:
                            break

                        result = self.api_client.get_current_price(stock_code)

                        # API 응답 전체 로깅 (디버깅용) - 한 종목만
                        if stock_code == self.stock_codes[0]:  # 첫 번째 종목만 전체 로깅
                            logger.info(f"📊 {stock_code} 전체 API 응답: {result}")

                        if result.get('return_code') == 0:
                            # API 응답이 flat 구조임 (output 키 없음)
                            # 가격 필드는 '+98800' 형식이므로 int() 변환 시 자동으로 부호 처리됨

                            # 틱 데이터 형식으로 변환
                            tick_data = {
                                'stock_code': stock_code,
                                'time': datetime.now().strftime('%H%M%S'),
                                'price': int(result.get('cur_prc', 0)),
                                'volume': int(result.get('trde_qty', 0)),  # 거래량
                                'change_rate': float(result.get('flu_rt', 0)),  # 등락율
                                'high': int(result.get('high_pric', 0)),
                                'low': int(result.get('low_pric', 0)),
                                'open': int(result.get('open_pric', 0)),
                                'accumulated_volume': int(result.get('trde_qty', 0))
                            }

                            # 콜백 호출
                            self.on_tick_received(tick_data)

                        else:
                            logger.warning(f"⚠️ {stock_code} 현재가 조회 실패: {result.get('return_msg')}")

                    # 다음 폴링까지 대기
                    time.sleep(self.polling_interval)

                except Exception as e:
                    logger.error(f"❌ 폴링 오류: {e}")
                    time.sleep(self.polling_interval)

        self.polling_thread = threading.Thread(target=polling_job, daemon=True)
        self.polling_thread.start()

        logger.info("✅ REST API 폴링 모드 활성화 완료")

    def _switch_to_polling_mode(self):
        """WebSocket에서 폴링 모드로 전환"""
        if self.collection_mode == 'polling':
            return

        logger.info("🔄 WebSocket → REST API 폴링 모드 전환 중...")

        # WebSocket 종료
        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None

        # 폴링 모드로 전환
        self.collection_mode = 'polling'
        self._start_polling_mode()

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
            self.last_tick_time = datetime.now()

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
                mode_str = "WebSocket" if self.collection_mode == 'websocket' else "REST API 폴링"
                logger.info(f"💾 DB 저장 ({mode_str}): {count:,}건 (총 {self.tick_count:,}건 수집)")

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
            logger.info(f"수집 통계 ({self.collection_mode.upper()} 모드)")
            logger.info("=" * 60)
            logger.info(f"총 수집 건수: {self.tick_count:,}건")
            logger.info(f"수집 시간: {elapsed:.1f}초")
            logger.info(f"평균 수집 속도: {rate:.1f}건/초")
            logger.info("=" * 60)

        logger.info("✅ 수집 중지 완료")

    def add_stock(self, stock_code: str, stock_name: str = None) -> dict:
        """
        실시간으로 종목 추가

        Args:
            stock_code: 종목 코드 (6자리)
            stock_name: 종목명 (선택, 없으면 API로 조회)

        Returns:
            dict: 추가 결과 {'success': bool, 'message': str, 'stock_name': str}
        """
        # 이미 수집 중인지 확인
        if stock_code in self.stock_codes:
            return {
                'success': False,
                'message': f'종목 {stock_code}는 이미 수집 중입니다',
                'stock_name': self.stock_info.get(stock_code, stock_code)
            }

        # 종목명이 없으면 API로 조회
        if not stock_name:
            try:
                result = self.api_client.get_current_price(stock_code)
                if result.get('return_code') == 0:
                    stock_name = result.get('stk_nm', stock_code)
                else:
                    stock_name = stock_code
                    logger.warning(f"⚠️ {stock_code} 종목명 조회 실패, 코드로 표시합니다")
            except Exception as e:
                stock_name = stock_code
                logger.error(f"❌ {stock_code} 종목 정보 조회 오류: {e}")

        # 종목 추가
        self.stock_codes.append(stock_code)
        self.stock_info[stock_code] = stock_name

        # WebSocket 모드면 실시간 구독 추가
        if self.collection_mode == 'websocket' and self.ws_client and self.ws_client.is_connected:
            try:
                self.ws_client.subscribe_tick([stock_code], self.on_tick_received)
                logger.info(f"✅ WebSocket 구독 추가: {stock_code} ({stock_name})")
            except Exception as e:
                logger.error(f"❌ WebSocket 구독 실패: {e}")

        # 시장 구분 조회
        market_type = "KRX"
        try:
            market_type = self.api_client.get_market_type(stock_code)
            logger.debug(f"종목 {stock_code} 시장 구분: {market_type}")
        except Exception as e:
            logger.warning(f"⚠️ 시장 구분 조회 실패: {e}")

        # 종목 마스터 정보 저장
        try:
            from sub_server.services.storage_service import TickStorageService
            storage = TickStorageService()
            storage.insert_stock_master(stock_code, stock_name, market_type)
            storage.close()
        except Exception as e:
            logger.warning(f"⚠️ 종목 마스터 저장 실패: {e}")

        # Redis에 저장
        if self.redis:
            try:
                self.redis.add_custom_stock(stock_code, stock_name)
                logger.debug(f"Redis에 커스텀 종목 저장: {stock_code}")
            except Exception as e:
                logger.warning(f"⚠️ Redis 저장 실패: {e}")

        logger.info(f"📌 종목 추가 완료: {stock_code} ({stock_name}) - 총 {len(self.stock_codes)}개 수집 중")

        return {
            'success': True,
            'message': f'종목 {stock_code} ({stock_name}) 추가 완료',
            'stock_name': stock_name
        }

    def remove_stock(self, stock_code: str) -> dict:
        """
        실시간으로 종목 제거

        Args:
            stock_code: 종목 코드

        Returns:
            dict: 제거 결과 {'success': bool, 'message': str}
        """
        if stock_code not in self.stock_codes:
            return {
                'success': False,
                'message': f'종목 {stock_code}는 수집 중이 아닙니다'
            }

        stock_name = self.stock_info.get(stock_code, stock_code)
        self.stock_codes.remove(stock_code)
        self.stock_info.pop(stock_code, None)

        # Redis에서 제거
        if self.redis:
            try:
                self.redis.remove_custom_stock(stock_code)
                logger.debug(f"Redis에서 커스텀 종목 제거: {stock_code}")
            except Exception as e:
                logger.warning(f"⚠️ Redis 제거 실패: {e}")

        logger.info(f"📌 종목 제거 완료: {stock_code} ({stock_name}) - 총 {len(self.stock_codes)}개 수집 중")

        return {
            'success': True,
            'message': f'종목 {stock_code} ({stock_name}) 제거 완료'
        }

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
            'collection_mode': self.collection_mode,
            'tick_count': self.tick_count,
            'elapsed_seconds': elapsed,
            'ticks_per_second': rate,
            'buffer_size': len(self.buffer),
            'stock_count': len(self.stock_codes),
            'stock_info': self.stock_info
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
        거래대금 TOP N 종목 수집 (개선된 버전)

        Args:
            limit: 조회할 종목 수

        Returns:
            list: 종목 리스트
                [
                    {
                        'stock_code': '005930',
                        'stock_name': '삼성전자',
                        'trading_value': 500000000000,
                        'current_price': 75000,
                        'change_rate': 1.35,
                        'volume': 10000000,
                        'rank_position': 1,
                        'collected_at': datetime
                    },
                    ...
                ]
        """
        logger.info(f"📊 거래대금 TOP {limit} 종목 수집 중...")

        try:
            # ka10032 API를 사용하여 거래대금 상위 종목 조회 (1회 호출로 완료)
            top_stocks_raw = self.api_client.get_top_trading_value(
                market_type="0",  # 전체
                sort_type="1",    # 거래대금 순
                target_type="1",  # 관리종목 제외
                limit=limit
            )

            if not top_stocks_raw:
                logger.warning("⚠️ 거래대금 상위 종목 조회 결과 없음")
                return []

            # 데이터 변환
            top_stocks = []
            for i, stock in enumerate(top_stocks_raw, 1):
                top_stocks.append({
                    'stock_code': stock.get('stk_cd', ''),
                    'stock_name': stock.get('stk_nm', ''),
                    'trading_value': int(stock.get('trde_val', 0)),
                    'current_price': int(stock.get('cur_pr', 0)),
                    'change_rate': float(stock.get('chg_rt', 0)),
                    'volume': int(stock.get('trde_vol', 0)),
                    'rank_position': i,
                    'collected_at': datetime.now()
                })

            # DB 저장
            if top_stocks:
                self.storage.insert_trading_volume_rank(top_stocks)
                logger.info(f"✅ 거래대금 TOP {len(top_stocks)}개 종목 수집 완료")

                # 상위 5개 로깅
                logger.info("=" * 60)
                logger.info("📈 거래대금 TOP 5")
                logger.info("=" * 60)
                for stock in top_stocks[:5]:
                    logger.info(
                        f"{stock['rank_position']:2d}위 | "
                        f"{stock['stock_name']:10s} ({stock['stock_code']}) | "
                        f"거래대금: {stock['trading_value']:>15,}원 | "
                        f"현재가: {stock['current_price']:>7,}원 | "
                        f"등락율: {stock['change_rate']:>6.2f}%"
                    )
                logger.info("=" * 60)

            return top_stocks

        except Exception as e:
            logger.error(f"❌ 거래대금 랭킹 수집 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
