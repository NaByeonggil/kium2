"""
키움 API 디버깅 스크립트
실제 응답 내용 확인
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

appkey = os.getenv("KIWOOM_APP_KEY")
secretkey = os.getenv("KIWOOM_SECRET_KEY")
is_mock = os.getenv("KIWOOM_IS_MOCK", "true").lower() == "true"

print("=" * 60)
print("키움 API 디버깅")
print("=" * 60)
print(f"App Key: {appkey[:20]}...")
print(f"Secret Key: {secretkey[:20]}...")
print(f"모의투자 모드: {is_mock}")
print()

# URL 설정
if is_mock:
    base_url = "https://mockapi.kiwoom.com"
else:
    base_url = "https://api.kiwoom.com"

url = f"{base_url}/oauth2/token"

print(f"요청 URL: {url}")
print()

# 요청 데이터
headers = {
    "Content-Type": "application/json;charset=UTF-8"
}

body = {
    "grant_type": "client_credentials",
    "appkey": appkey,
    "secretkey": secretkey
}

print("요청 헤더:")
print(headers)
print()

print("요청 본문:")
print(body)
print()

# 실제 요청
print("API 호출 중...")
try:
    response = requests.post(url, headers=headers, json=body, timeout=10)

    print(f"HTTP 상태 코드: {response.status_code}")
    print(f"응답 헤더: {dict(response.headers)}")
    print()

    print("응답 본문 (Raw):")
    print(response.text)
    print()

    if response.status_code == 200:
        try:
            data = response.json()
            print("응답 JSON:")
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ JSON 파싱 실패: {e}")
    else:
        print(f"❌ HTTP 오류: {response.status_code}")
        print(f"응답: {response.text}")

except Exception as e:
    print(f"❌ 요청 실패: {e}")
    import traceback
    traceback.print_exc()
