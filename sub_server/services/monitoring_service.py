"""
모니터링 서비스

실시간 시스템 상태 조회 및 모니터링
"""

import psutil
import platform
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from sub_server.services.storage_service import TickStorageService

logger = logging.getLogger(__name__)


class MonitoringService:
    """모니터링 서비스 클래스"""

    def __init__(self, tick_collector=None):
        """
        초기화

        Args:
            tick_collector: TickCollector 인스턴스 (선택)
        """
        self.tick_collector = tick_collector
        self.start_time = datetime.now()
        self.storage = TickStorageService()

    def get_system_info(self) -> Dict[str, Any]:
        """
        시스템 정보 조회

        Returns:
            dict: 시스템 정보
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': cpu_percent,
                'memory_total_gb': round(memory.total / (1024 ** 3), 2),
                'memory_used_gb': round(memory.used / (1024 ** 3), 2),
                'memory_percent': memory.percent,
                'disk_total_gb': round(disk.total / (1024 ** 3), 2),
                'disk_used_gb': round(disk.used / (1024 ** 3), 2),
                'disk_percent': disk.percent
            }
        except Exception as e:
            logger.error(f"시스템 정보 조회 실패: {e}")
            return {}

    def get_collector_stats(self) -> Dict[str, Any]:
        """
        수집기 통계 조회

        Returns:
            dict: 수집기 통계
        """
        if not self.tick_collector:
            return {
                'status': 'not_initialized',
                'is_running': False
            }

        try:
            stats = self.tick_collector.get_stats()

            return {
                'status': 'running' if stats['is_running'] else 'stopped',
                'is_running': stats['is_running'],
                'tick_count': stats['tick_count'],
                'elapsed_seconds': stats['elapsed_seconds'],
                'ticks_per_second': round(stats['ticks_per_second'], 2),
                'buffer_size': stats['buffer_size'],
                'stock_count': stats['stock_count'],
                'buffer_usage_percent': round(
                    (stats['buffer_size'] / self.tick_collector.buffer_size * 100), 2
                ) if self.tick_collector.buffer_size > 0 else 0,
                'collection_mode': stats.get('collection_mode', 'unknown')
            }
        except Exception as e:
            logger.error(f"수집기 통계 조회 실패: {e}")
            return {
                'status': 'error',
                'is_running': False,
                'error_message': str(e)
            }

    def get_collecting_stocks(self) -> Dict[str, Any]:
        """
        현재 수집 중인 종목 목록 조회

        Returns:
            dict: 수집 중인 종목 정보 (시장 구분 포함)
        """
        if not self.tick_collector:
            return {
                'status': 'not_initialized',
                'stocks': [],
                'kospi': [],
                'kosdaq': [],
                'stock_count': 0
            }

        try:
            stock_codes = self.tick_collector.stock_codes or []
            stock_info = self.tick_collector.stock_info or {}

            # DB에서 시장 구분 정보 조회
            market_types = {}
            if stock_codes:
                try:
                    market_types = self.storage.get_stock_market_types(stock_codes)
                except Exception as e:
                    logger.warning(f"시장 구분 조회 실패: {e}")

            # 시장 구분 판별 함수 (DB에 없거나 KRX인 경우 코드로 판별)
            def get_market_type(code: str) -> str:
                db_market = market_types.get(code, 'KRX').upper()
                if db_market in ('KOSPI', 'KOSDAQ', 'ETF'):
                    return db_market

                # 주요 코스피 종목 (코드 패턴으로 판별 어려운 경우)
                kospi_codes = {
                    '005930', '000660', '035420', '005380', '051910',  # 삼성전자, SK하이닉스, NAVER, 현대차, LG화학
                    '006400', '035720', '068270', '207940', '005490',  # 삼성SDI, 카카오, 셀트리온, 삼성바이오로직스, POSCO홀딩스
                    '003670', '000270', '105560', '028260', '055550',  # 포스코퓨처엠, 기아, KB금융, 삼성물산, 신한지주
                    '012330', '066570', '003550', '096770', '032830',  # 현대모비스, LG전자, LG, SK이노베이션, 삼성생명
                    '017670', '034730', '009150', '018260', '086790',  # SK텔레콤, SK, 삼성전기, 삼성에스디에스, 하나금융지주
                    '015760', '010130', '033780', '011200', '010950',  # 한국전력, 고려아연, KT&G, HMM, S-Oil
                    '009540', '000810', '036570', '024110', '004020',  # 한국조선해양, 삼성화재, 엔씨소프트, 기업은행, 현대제철
                    '010140', '002790', '034020', '047050', '090430',  # 삼성중공업, 아모레퍼시픽, 두산에너빌리티, 포스코인터내셔널, 아모레G
                    '326030', '003490', '000100', '011070', '036460',  # SK바이오팜, 대한항공, 유한양행, LG이노텍, 한국가스공사
                    '316140', '161390', '259960', '030200', '352820',  # 우리금융지주, 한국타이어앤테크놀로지, 크래프톤, KT, 하이브
                    '071050', '097950', '010620', '251270', '180640',  # 한국금융지주, CJ제일제당, 현대건설, 넷마블, 한진칼
                    '004170', '000720', '003410', '021240', '008930',  # 신세계, 현대건설, 쌍용C&E, 코웨이, 한미사이언스
                    '016360', '138040', '139480', '009830', '047810',  # 삼성증권, 메리츠금융지주, 이마트, 한화솔루션, 한국항공우주
                    '042660', '060250',  # 한화오션, NHN KCP
                }

                # 주요 코스닥 종목
                kosdaq_codes = {
                    '247540', '086520', '091990', '035760', '293490',  # 에코프로비엠, 에코프로, 셀트리온헬스케어, CJ ENM, 카카오게임즈
                    '041510', '028300', '112040', '145020', '196170',  # 에스엠, HLB, 위메이드, 휴젤, 알테오젠
                    '215600', '357780', '039030', '263750', '403870',  # 신라젠, 솔루스첨단소재, 이오테크닉스, 펄어비스, HPSP
                    '095340',  # ISC
                }

                if code in kospi_codes:
                    return 'KOSPI'
                elif code in kosdaq_codes:
                    return 'KOSDAQ'

                # 코드 패턴 기반 추정 (fallback)
                # 일반적으로 0으로 시작하면 코스피 가능성 높음
                if code.startswith('0'):
                    return 'KOSPI'

                return 'KRX'

            # 종목 정보 구성 (시장별 분류)
            kospi_list = []
            kosdaq_list = []
            other_stocks = []

            if stock_codes:
                for code in stock_codes:
                    market = get_market_type(code)
                    stock_data = {
                        'stock_code': code,
                        'stock_name': stock_info.get(code, '-'),
                        'market_type': market
                    }

                    if market == 'KOSPI':
                        kospi_list.append(stock_data)
                    elif market == 'KOSDAQ':
                        kosdaq_list.append(stock_data)
                    else:
                        other_stocks.append(stock_data)

            # 전체 종목 목록 (하위 호환성)
            all_stocks = kospi_list + kosdaq_list + other_stocks

            return {
                'status': 'success',
                'stocks': all_stocks,
                'kospi': kospi_list,
                'kosdaq': kosdaq_list,
                'other': other_stocks,
                'stock_count': len(stock_codes),
                'kospi_count': len(kospi_list),
                'kosdaq_count': len(kosdaq_list),
                'collection_mode': self.tick_collector.collection_mode
            }
        except Exception as e:
            logger.error(f"수집 종목 조회 실패: {e}")
            return {
                'status': 'error',
                'stocks': [],
                'kospi': [],
                'kosdaq': [],
                'stock_count': 0,
                'error_message': str(e)
            }

    def get_database_stats(self) -> Dict[str, Any]:
        """
        데이터베이스 통계 조회

        Returns:
            dict: 데이터베이스 통계
        """
        try:
            tick_count_today = self.storage.get_tick_count_today()
            db_size = self.storage.get_database_size()

            return {
                'tick_count_today': tick_count_today,
                'database_size': db_size,
                'status': 'connected'
            }
        except Exception as e:
            logger.error(f"데이터베이스 통계 조회 실패: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }
        finally:
            if hasattr(self, 'storage'):
                self.storage.close()
                self.storage = TickStorageService()  # 재생성

    def get_uptime_info(self) -> Dict[str, Any]:
        """
        가동 시간 정보 조회

        Returns:
            dict: 가동 시간 정보
        """
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        return {
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': f"{int(hours)}시간 {int(minutes)}분 {int(seconds)}초"
        }

    def get_full_status(self) -> Dict[str, Any]:
        """
        전체 상태 조회

        Returns:
            dict: 전체 시스템 상태
        """
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system': self.get_system_info(),
            'collector': self.get_collector_stats(),
            'database': self.get_database_stats(),
            'uptime': self.get_uptime_info()
        }

    def get_health_status(self) -> Dict[str, Any]:
        """
        헬스 체크 (간단한 상태 확인)

        Returns:
            dict: 헬스 상태
        """
        try:
            collector_stats = self.get_collector_stats()
            db_stats = self.get_database_stats()
            system_info = self.get_system_info()

            # 상태 판정
            is_healthy = True
            issues = []

            # 1. 수집기 상태 확인
            if not collector_stats.get('is_running'):
                is_healthy = False
                issues.append("수집기가 실행 중이지 않습니다")

            # 2. 버퍼 사용률 확인 (90% 이상이면 경고)
            buffer_usage = collector_stats.get('buffer_usage_percent', 0)
            if buffer_usage >= 90:
                issues.append(f"버퍼 사용률이 높습니다 ({buffer_usage:.1f}%)")

            # 3. 메모리 사용률 확인 (90% 이상이면 경고)
            memory_percent = system_info.get('memory_percent', 0)
            if memory_percent >= 90:
                is_healthy = False
                issues.append(f"메모리 사용률이 높습니다 ({memory_percent:.1f}%)")

            # 4. CPU 사용률 확인 (95% 이상이면 경고)
            cpu_percent = system_info.get('cpu_percent', 0)
            if cpu_percent >= 95:
                issues.append(f"CPU 사용률이 높습니다 ({cpu_percent:.1f}%)")

            # 5. 디스크 사용률 확인 (90% 이상이면 경고)
            disk_percent = system_info.get('disk_percent', 0)
            if disk_percent >= 90:
                is_healthy = False
                issues.append(f"디스크 사용률이 높습니다 ({disk_percent:.1f}%)")

            # 6. DB 연결 확인
            if db_stats.get('status') == 'error':
                is_healthy = False
                issues.append("데이터베이스 연결 오류")

            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'is_healthy': is_healthy,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'issues': issues
            }

        except Exception as e:
            logger.error(f"헬스 체크 실패: {e}")
            return {
                'status': 'error',
                'is_healthy': False,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'issues': [f"헬스 체크 오류: {str(e)}"]
            }

    def close(self):
        """리소스 정리"""
        if hasattr(self, 'storage'):
            self.storage.close()
