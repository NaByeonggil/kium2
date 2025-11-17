#!/usr/bin/env python3
"""
종목 리스트 API 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sub_server.api.kiwoom_client import KiwoomAPIClient
import os
from dotenv import load_dotenv
import json

# 환경변수 로드
load_dotenv()

def main():
    print("=" * 60)
    print("종목 리스트 API 테스트")
    print("=" * 60)

    # API 클라이언트 생성
    appkey = os.getenv('KIWOOM_APP_KEY')
    secretkey = os.getenv('KIWOOM_SECRET_KEY')
    is_mock = os.getenv('KIWOOM_IS_MOCK', 'false').lower() == 'true'

    print(f"\n모의투자 모드: {is_mock}")

    client = KiwoomAPIClient(appkey, secretkey, is_mock)

    # 1. 전체 종목 리스트 조회
    print("\n1. 전체 종목 리스트 조회 (mrkt_tp=0)")
    print("-" * 60)

    result = client.get_stock_list("0")

    print(f"Return Code: {result.get('return_code')}")
    print(f"Return Message: {result.get('return_msg')}")

    if result.get('return_code') == 0:
        data = result.get('data', [])
        print(f"총 종목 수: {len(data)}")

        if data:
            print(f"\n첫 3개 종목:")
            for i, stock in enumerate(data[:3], 1):
                print(f"  {i}. {stock}")
    else:
        print(f"❌ 오류: {result.get('return_msg')}")

    # 2. 코스피만 조회
    print("\n\n2. 코스피 종목 조회 (mrkt_tp=1)")
    print("-" * 60)

    result = client.get_stock_list("1")

    print(f"Return Code: {result.get('return_code')}")
    print(f"Return Message: {result.get('return_msg')}")

    if result.get('return_code') == 0:
        data = result.get('data', [])
        print(f"코스피 종목 수: {len(data)}")

    # 3. 응답 전체 출력 (디버깅용)
    print("\n\n3. 응답 전체 (JSON)")
    print("-" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()
