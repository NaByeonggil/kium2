"""
통합 테스트 스크립트

Sub Server 전체 시스템 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
import time
import requests

# 환경변수 로드
load_dotenv()

print("=" * 80)
print("GSLTS Sub Server 통합 테스트")
print("=" * 80)
print()


def test_environment():
    """환경변수 테스트"""
    print("1️⃣ 환경변수 확인")
    print("-" * 80)

    required_vars = [
        'KIWOOM_APP_KEY',
        'KIWOOM_SECRET_KEY',
        'KIWOOM_IS_MOCK',
        'DB_HOST',
        'DB_USER',
        'DB_NAME'
    ]

    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        display_value = value[:20] + "..." if value and len(value) > 20 else value
        print(f"{status} {var}: {display_value}")

        if not value:
            all_ok = False

    print()
    return all_ok


def test_imports():
    """모듈 임포트 테스트"""
    print("2️⃣ 모듈 임포트 테스트")
    print("-" * 80)

    modules = {
        'API Client': 'from sub_server.api.kiwoom_client import KiwoomAPIClient',
        'WebSocket': 'from sub_server.api.websocket_client import KiwoomWebSocket',
        'Storage': 'from sub_server.services.storage_service import TickStorageService',
        'Tick Collector': 'from sub_server.collectors.tick_collector import TickCollector',
        'Monitoring': 'from sub_server.services.monitoring_service import MonitoringService',
        'Dashboard': 'from sub_server.monitoring.dashboard import app as dashboard_app',
        'Logging': 'from sub_server.config.logging_config import setup_logging',
        'Main Server': 'from sub_server.main import SubServer'
    }

    all_ok = True
    for name, import_stmt in modules.items():
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            all_ok = False

    print()
    return all_ok


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("3️⃣ 데이터베이스 연결 테스트")
    print("-" * 80)

    try:
        from sub_server.services.storage_service import TickStorageService

        storage = TickStorageService()
        print(f"✅ DB 연결 성공: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")

        # DB 크기 조회
        try:
            db_size = storage.get_database_size()
            print(f"✅ DB 크기: {db_size}")
        except Exception as e:
            print(f"⚠️ DB 크기 조회 실패 (테이블이 없을 수 있음): {e}")

        storage.close()
        print()
        return True

    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        print()
        return False


def test_api_connection():
    """키움 API 연결 테스트"""
    print("4️⃣ 키움 API 연결 테스트")
    print("-" * 80)

    try:
        from sub_server.api.kiwoom_client import KiwoomAPIClient

        appkey = os.getenv('KIWOOM_APP_KEY')
        secretkey = os.getenv('KIWOOM_SECRET_KEY')
        is_mock = os.getenv('KIWOOM_IS_MOCK', 'true').lower() == 'true'

        client = KiwoomAPIClient(appkey, secretkey, is_mock)

        print(f"✅ API 클라이언트 생성 성공")
        print(f"   모의투자: {is_mock}")

        # 토큰 발급 테스트
        try:
            token = client.token
            if token:
                print(f"✅ OAuth 토큰 발급 성공: {token[:20]}...")
                return True
            else:
                print(f"❌ OAuth 토큰 발급 실패")
                return False
        except Exception as e:
            print(f"❌ OAuth 토큰 발급 실패: {e}")
            return False

    except Exception as e:
        print(f"❌ API 클라이언트 생성 실패: {e}")
        return False
    finally:
        print()


def test_monitoring_service():
    """모니터링 서비스 테스트"""
    print("5️⃣ 모니터링 서비스 테스트")
    print("-" * 80)

    try:
        from sub_server.services.monitoring_service import MonitoringService

        monitor = MonitoringService()

        # 시스템 정보 조회
        system_info = monitor.get_system_info()
        print(f"✅ 시스템 정보 조회 성공")
        print(f"   CPU: {system_info.get('cpu_percent', 0):.1f}%")
        print(f"   메모리: {system_info.get('memory_percent', 0):.1f}%")

        # 헬스 체크
        health = monitor.get_health_status()
        print(f"✅ 헬스 체크: {health.get('status', 'unknown')}")

        monitor.close()
        print()
        return True

    except Exception as e:
        print(f"❌ 모니터링 서비스 테스트 실패: {e}")
        print()
        return False


def test_logging_system():
    """로깅 시스템 테스트"""
    print("6️⃣ 로깅 시스템 테스트")
    print("-" * 80)

    try:
        from sub_server.config.logging_config import setup_logging, get_log_config_from_env
        import logging

        # 로깅 설정
        log_config = get_log_config_from_env()
        setup_logging(**log_config)

        logger = logging.getLogger("test")
        logger.info("테스트 로그 메시지")

        print(f"✅ 로깅 시스템 초기화 성공")
        print(f"   로그 디렉토리: {log_config['log_dir']}")
        print(f"   로그 레벨: {log_config['log_level']}")
        print()
        return True

    except Exception as e:
        print(f"❌ 로깅 시스템 테스트 실패: {e}")
        print()
        return False


def test_dashboard_startup():
    """대시보드 시작 테스트"""
    print("7️⃣ 대시보드 시작 테스트")
    print("-" * 80)

    try:
        from sub_server.monitoring.dashboard import app as dashboard_app
        import threading
        import uvicorn

        port = int(os.getenv('SUB_SERVER_PORT', 8001))

        # 대시보드를 별도 스레드에서 시작
        def run_dashboard():
            uvicorn.run(dashboard_app, host="127.0.0.1", port=port, log_level="error")

        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()

        # 서버 시작 대기
        print(f"   대시보드 시작 중... (포트 {port})")
        time.sleep(3)

        # API 호출 테스트
        try:
            response = requests.get(f"http://localhost:{port}/api/health", timeout=5)

            if response.status_code in [200, 503]:  # 503도 허용 (collector 미초기화 상태)
                print(f"✅ 대시보드 API 응답: HTTP {response.status_code}")
                print(f"   대시보드 URL: http://localhost:{port}/dashboard")
                print()
                return True
            else:
                print(f"❌ 대시보드 API 응답 실패: HTTP {response.status_code}")
                print()
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 대시보드 접속 실패: {e}")
            print()
            return False

    except Exception as e:
        print(f"❌ 대시보드 시작 실패: {e}")
        print()
        return False


def main():
    """메인 테스트 실행"""
    results = {
        "환경변수": test_environment(),
        "모듈 임포트": test_imports(),
        "데이터베이스": test_database_connection(),
        "키움 API": test_api_connection(),
        "모니터링": test_monitoring_service(),
        "로깅": test_logging_system(),
        "대시보드": test_dashboard_startup()
    }

    # 결과 요약
    print("=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status} - {name}")

    print()
    print(f"통과: {passed}/{total} ({passed/total*100:.1f}%)")
    print()

    if passed == total:
        print("🎉 모든 테스트 통과!")
        print()
        print("다음 단계:")
        print("1. MariaDB 설치 및 설정 (아직 안 했다면)")
        print("2. database/schema.sql 실행하여 테이블 생성")
        print("3. python sub_server/main.py 실행하여 Sub Server 시작")
        print()
    else:
        print("⚠️ 일부 테스트 실패. 위의 오류 메시지를 확인하세요.")
        print()


if __name__ == "__main__":
    main()
