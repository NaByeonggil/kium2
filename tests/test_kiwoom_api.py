"""
키움증권 REST API 연결 테스트

실행 방법:
1. .env 파일에 App Key, Secret Key 입력
2. python tests/test_kiwoom_api.py

필수 패키지:
pip install requests python-dotenv websocket-client
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import logging
import time

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_rest_api():
    """REST API 테스트"""
    from sub_server.api.kiwoom_client import KiwoomAPIClient

    print("\n" + "=" * 60)
    print("키움증권 REST API 연결 테스트")
    print("=" * 60 + "\n")

    # 환경변수 확인
    appkey = os.getenv("KIWOOM_APP_KEY")
    secretkey = os.getenv("KIWOOM_SECRET_KEY")
    is_mock = os.getenv("KIWOOM_IS_MOCK", "true").lower() == "true"

    if not appkey or not secretkey:
        print("❌ .env 파일에 KIWOOM_APP_KEY, KIWOOM_SECRET_KEY를 설정해주세요")
        return False

    if appkey == "your_app_key_here":
        print("⚠️ .env 파일에서 실제 App Key를 입력해주세요")
        print("\n키움증권 홈페이지 → 트레이딩 채널 → 키움 REST API → App Key 관리")
        return False

    print(f"모의투자 모드: {is_mock}\n")

    try:
        # 1. API 클라이언트 초기화 (자동으로 토큰 발급)
        print("1️⃣ OAuth 토큰 발급 중...")
        client = KiwoomAPIClient(appkey, secretkey, is_mock)
        print(f"✅ 토큰 발급 성공!")
        print(f"   Token: {client.token[:50]}...")
        print(f"   만료 시간: {client.token_expires}\n")

        # 2. 삼성전자 현재가 조회
        print("2️⃣ 삼성전자(005930) 현재가 조회 중...")
        price_info = client.get_current_price("005930")

        if price_info.get('return_code') == 0:
            print(f"✅ 현재가 조회 성공!")
            print(f"   종목명: {price_info.get('stk_nm')}")
            print(f"   현재가: {price_info.get('now_uv')}원")
            print(f"   전일대비: {price_info.get('prdy_vrss')}원 ({price_info.get('prdy_ctrt')}%)")
            print(f"   거래량: {price_info.get('acml_vol')}\n")
        else:
            print(f"❌ 현재가 조회 실패: {price_info.get('return_msg')}\n")
            return False

        # 3. 계좌 잔고 조회 (모의투자만)
        if is_mock:
            print("3️⃣ 계좌 잔고 조회 중...")
            balance = client.get_balance()

            if balance.get('return_code') == 0:
                print(f"✅ 계좌 조회 성공!")
                print(f"   총평가금액: {balance.get('tot_evlt_amt', 0)}원")
                print(f"   총평가손익: {balance.get('tot_evlt_pl', 0)}원")
                print(f"   보유 종목 수: {len(balance.get('data', []))}개\n")
            else:
                print(f"⚠️ 계좌 조회: {balance.get('return_msg')}\n")

        print("=" * 60)
        print("✅ REST API 테스트 완료!")
        print("=" * 60 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_websocket():
    """WebSocket 테스트"""
    from sub_server.api.kiwoom_client import KiwoomAPIClient
    from sub_server.api.websocket_client import KiwoomWebSocket

    print("\n" + "=" * 60)
    print("키움증권 WebSocket 연결 테스트")
    print("=" * 60 + "\n")

    # 환경변수 확인
    appkey = os.getenv("KIWOOM_APP_KEY")
    secretkey = os.getenv("KIWOOM_SECRET_KEY")
    is_mock = os.getenv("KIWOOM_IS_MOCK", "true").lower() == "true"

    if appkey == "your_app_key_here":
        print("⚠️ REST API 테스트를 먼저 통과해주세요\n")
        return False

    try:
        # 1. 토큰 발급
        print("1️⃣ OAuth 토큰 발급 중...")
        client = KiwoomAPIClient(appkey, secretkey, is_mock)
        token = client.token
        print(f"✅ 토큰 발급 완료\n")

        # 2. WebSocket 연결
        print("2️⃣ WebSocket 연결 중...")
        ws_client = KiwoomWebSocket(token, is_mock)
        ws_client.connect()

        if not ws_client.is_connected:
            print("❌ WebSocket 연결 실패\n")
            return False

        print(f"✅ WebSocket 연결 성공!\n")

        # 3. 실시간 체결 구독
        tick_count = 0

        def on_tick_received(tick_data):
            nonlocal tick_count
            tick_count += 1
            print(f"📊 [{tick_count}] {tick_data['stock_code']} | "
                  f"시간: {tick_data['time']} | "
                  f"가격: {tick_data['price']:,}원 | "
                  f"거래량: {tick_data['volume']:,}주")

        print("3️⃣ 삼성전자, SK하이닉스 실시간 체결 구독 중...")
        ws_client.subscribe_tick(["005930", "000660"], on_tick_received)

        # 10초간 데이터 수신
        print(f"⏱️ 10초간 실시간 데이터 수신 중...\n")
        time.sleep(10)

        # 연결 종료
        ws_client.close()

        print(f"\n총 수신: {tick_count}건")
        print("=" * 60)
        print("✅ WebSocket 테스트 완료!")
        print("=" * 60 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 키움증권 API 통합 테스트 시작\n")

    # 1. REST API 테스트
    rest_ok = test_rest_api()

    if rest_ok:
        # 2. WebSocket 테스트 (선택)
        answer = input("\nWebSocket 테스트를 진행하시겠습니까? (y/n): ")
        if answer.lower() == 'y':
            ws_ok = test_websocket()
        else:
            print("\n⏭️ WebSocket 테스트 건너뛰기")
            ws_ok = True
    else:
        ws_ok = False

    # 최종 결과
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"REST API: {'✅ 성공' if rest_ok else '❌ 실패'}")
    print(f"WebSocket: {'✅ 성공' if ws_ok else '⏭️ 건너뜀'}")
    print("=" * 60 + "\n")

    if rest_ok:
        print("🎉 다음 단계: Sub Server 개발")
        print("   - 틱데이터 수집 엔진 구현")
        print("   - 데이터베이스 연동")
        print("   - 실시간 모니터링 대시보드\n")
    else:
        print("❌ App Key/Secret Key를 확인하고 다시 시도해주세요\n")
