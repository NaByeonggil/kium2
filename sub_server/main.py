"""
Sub Server 메인 엔트리포인트

24시간 틱데이터 수집 서버
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
import time
import signal
import logging
from datetime import datetime

from sub_server.api.kiwoom_client import KiwoomAPIClient
from sub_server.collectors.tick_collector import TickCollector, RankingCollector
from sub_server.services.storage_service import TickStorageService
from sub_server.config.logging_config import setup_logging, get_log_config_from_env
from sub_server.monitoring.dashboard import app as dashboard_app, set_tick_collector
import threading
import uvicorn

# 환경변수 로드
load_dotenv()

# 로깅 시스템 초기화
log_config = get_log_config_from_env()
setup_logging(**log_config)

logger = logging.getLogger(__name__)


class SubServer:
    """Sub Server 메인 클래스"""

    def __init__(self):
        """초기화"""
        # 환경변수 로드
        self.appkey = os.getenv("KIWOOM_APP_KEY")
        self.secretkey = os.getenv("KIWOOM_SECRET_KEY")
        self.is_mock = os.getenv("KIWOOM_IS_MOCK", "true").lower() == "true"

        if not self.appkey or not self.secretkey:
            raise ValueError("❌ KIWOOM_APP_KEY, KIWOOM_SECRET_KEY를 .env 파일에 설정해주세요")

        # API 클라이언트
        self.api_client = None

        # 수집기
        self.tick_collector = None
        self.ranking_collector = None

        # 모니터링 대시보드
        self.dashboard_thread = None
        self.dashboard_port = int(os.getenv('SUB_SERVER_PORT', 8001))

        # 상태
        self.is_running = False

    def initialize(self):
        """초기화"""
        logger.info("=" * 60)
        logger.info("Sub Server 초기화")
        logger.info("=" * 60)

        # 1. API 클라이언트 초기화
        logger.info(f"모의투자 모드: {self.is_mock}")
        self.api_client = KiwoomAPIClient(self.appkey, self.secretkey, self.is_mock)

        # 2. 수집기 초기화
        self.tick_collector = TickCollector(self.appkey, self.secretkey, self.is_mock)
        self.ranking_collector = RankingCollector(self.api_client)

        # 3. 모니터링 대시보드 시작
        self._start_monitoring_dashboard()

        logger.info("✅ 초기화 완료\n")

    def start(self):
        """서버 시작"""
        self.is_running = True

        logger.info("=" * 60)
        logger.info("🚀 Sub Server 시작")
        logger.info("=" * 60)
        logger.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")

        try:
            # 1. 거래대금 TOP 50 종목 수집
            logger.info("📊 거래대금 TOP 50 종목 수집 중...")
            top_stocks = self.ranking_collector.collect_top_stocks(50)

            if not top_stocks:
                logger.warning("⚠️ 거래대금 TOP 종목을 가져올 수 없습니다")
                logger.info("💡 기본 종목 리스트 사용")

                # 기본 종목 리스트 (거래대금 상위 주요 종목)
                stock_codes = [
                    "005930",  # 삼성전자
                    "000660",  # SK하이닉스
                    "035420",  # NAVER
                    "005380",  # 현대차
                    "051910",  # LG화학
                    "006400",  # 삼성SDI
                    "035720",  # 카카오
                    "068270",  # 셀트리온
                    "207940",  # 삼성바이오로직스
                    "005490",  # POSCO홀딩스
                ]
            else:
                stock_codes = [stock['stock_code'] for stock in top_stocks]

            logger.info(f"✅ 수집 대상: {len(stock_codes)}개 종목\n")

            # 2. 틱데이터 수집 시작
            self.tick_collector.start(stock_codes)

            # 3. 메인 루프
            logger.info("=" * 60)
            logger.info("✅ Sub Server 가동 중...")
            logger.info("Ctrl+C로 종료")
            logger.info("=" * 60)
            logger.info("")

            # 통계 출력 주기 (초)
            stats_interval = 60

            last_stats_time = time.time()

            while self.is_running:
                time.sleep(1)

                # 주기적 통계 출력
                if time.time() - last_stats_time >= stats_interval:
                    self._print_stats()
                    last_stats_time = time.time()

        except KeyboardInterrupt:
            logger.info("\n⚠️ 사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()

    def _start_monitoring_dashboard(self):
        """모니터링 대시보드 시작 (별도 스레드)"""
        try:
            # 틱 수집기를 대시보드에 등록
            set_tick_collector(self.tick_collector)

            # 대시보드 서버를 별도 스레드에서 실행
            def run_dashboard():
                uvicorn.run(
                    dashboard_app,
                    host="0.0.0.0",
                    port=self.dashboard_port,
                    log_level="warning"  # 로그 레벨 낮춤 (INFO 메시지 감소)
                )

            self.dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
            self.dashboard_thread.start()

            logger.info(f"🌐 모니터링 대시보드 시작: http://localhost:{self.dashboard_port}/dashboard")
            logger.info(f"📊 API 엔드포인트: http://localhost:{self.dashboard_port}/api/status")

        except Exception as e:
            logger.error(f"❌ 모니터링 대시보드 시작 실패: {e}")

    def _print_stats(self):
        """통계 출력"""
        stats = self.tick_collector.get_stats()

        logger.info("")
        logger.info("=" * 60)
        logger.info("📊 실시간 통계")
        logger.info("=" * 60)
        logger.info(f"수집 상태: {'🟢 실행 중' if stats['is_running'] else '🔴 중지'}")
        logger.info(f"총 수집: {stats['tick_count']:,}건")
        logger.info(f"수집 속도: {stats['ticks_per_second']:.1f}건/초")
        logger.info(f"버퍼 크기: {stats['buffer_size']:,}건")
        logger.info(f"수집 종목: {stats['stock_count']}개")

        # DB 통계
        storage = TickStorageService()
        try:
            today_count = storage.get_tick_count_today()
            db_size = storage.get_database_size()

            logger.info(f"오늘 DB 저장: {today_count:,}건")
            logger.info(f"DB 크기: {db_size}")
        finally:
            storage.close()

        logger.info("=" * 60)
        logger.info("")

    def stop(self):
        """서버 중지"""
        if not self.is_running:
            return

        logger.info("")
        logger.info("=" * 60)
        logger.info("⏹️ Sub Server 종료 중...")
        logger.info("=" * 60)

        self.is_running = False

        # 틱 수집기 중지
        if self.tick_collector:
            self.tick_collector.stop()

        logger.info("✅ Sub Server 종료 완료")
        logger.info(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)


def main():
    """메인 함수"""
    # Sub Server 초기화 및 실행
    server = SubServer()

    # 시그널 핸들러 등록
    def signal_handler(sig, frame):
        logger.info("\n⚠️ 종료 시그널 수신")
        server.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 초기화
        server.initialize()

        # 서버 시작
        server.start()

    except Exception as e:
        logger.error(f"❌ 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
