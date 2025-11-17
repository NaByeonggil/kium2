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
                ) if self.tick_collector.buffer_size > 0 else 0
            }
        except Exception as e:
            logger.error(f"수집기 통계 조회 실패: {e}")
            return {
                'status': 'error',
                'is_running': False,
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
