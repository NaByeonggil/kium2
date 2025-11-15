# 키움 REST API 증권 거래 시스템 실행 계획서

> **프로젝트명**: Global Sector Linked Trading System (GSLTS)  
> **작성일**: 2025-11-15  
> **버전**: 3.0 (REST API + Sub Server 우선) ⭐ NEW  
> **총 예상 시간**: 220시간 (약 6주, 1인 기준)

---

## 🎉 대변화: REST API 사용!

### Windows COM → REST API로 전환

**기존 방식 (OpenAPI+)**:
- ❌ Windows 전용 COM 방식
- ❌ pywinauto, PyQt5 필요
- ❌ Linux/macOS 불가능
- ❌ 브라우저 사용 불가

**새로운 방식 (REST API)** ⭐:
- ✅ RESTful API + WebSocket
- ✅ OAuth 2.0 인증 (App Key/Secret Key)
- ✅ **크로스 플랫폼** (Windows, macOS, Linux)
- ✅ **브라우저에서 직접 매매 가능**
- ✅ requests, websockets만 있으면 OK

### REST API 핵심 장점

```python
# 기존 COM 방식
from PyQt5.QAxContainer import QAxWidget
kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")  # Windows만 가능

# 새로운 REST API 방식
import requests
response = requests.post("https://mockapi.kiwoom.com/oauth2/token")
# 어디서든 가능! 🚀
```

**207개 API 제공**:
- REST API: 199개
- WebSocket 실시간: 18개

---

## 📋 새로운 Phase 구성

| Phase | 기간 | 목표 | 핵심 기술 |
|-------|------|------|----------|
| Phase 0 | 1주 | 환경 구축 | App Key 발급 |
| **Phase 1** | **2주** | **Sub Server** | **REST API + WebSocket** ⭐ |
| Phase 2 | 4주 | Main Server | React + FastAPI |
| Phase 3 | 3주 | 섹터 연동 | 추천 알고리즘 |
| Phase 4 | 진행 중 | 프리미엄 | 수익화 |

---

## Phase 0: 환경 구축 (1주)

> **총 시간**: 12시간 (기존 15h → 3h 단축!)

### TASK-000: 개발 환경 초기 설정 [INFRA] - 3h

**산출물**:
```
/trading-system
  /frontend (React + Next.js)
  /backend (FastAPI)
  /sub-server (Data Hub)
  /database (SQL scripts)
  /docker
```

**완료 조건**:
- [ ] Git 저장소 생성
- [ ] Docker Compose 설정
- [ ] README.md 작성

**의존성**: 없음

---

### TASK-001: 키움 REST API 신청 [INTEGRATION] - 3h

**절차**:
1. **키움증권 홈페이지 로그인**
2. **REST API 신청**
   - 경로: 고객서비스 → 다운로드 → Open API → 키움 REST API
3. **IP 주소 등록** (최대 10개)
4. **App Key / Secret Key 발급**
   - 모의투자: mockapi.kiwoom.com
   - 실제투자: api.kiwoom.com

**테스트 코드**:
```python
import requests

# 토큰 발급 테스트
url = "https://mockapi.kiwoom.com/oauth2/token"
body = {
    "grant_type": "client_credentials",
    "appkey": "YOUR_APP_KEY",
    "secretkey": "YOUR_SECRET_KEY"
}
response = requests.post(url, json=body)
print(response.json())  # token 확인
```

**완료 조건**:
- [ ] App Key/Secret Key 발급
- [ ] 토큰 발급 성공
- [ ] .env 파일에 키 저장

**의존성**: 없음

---

### TASK-002: 데이터베이스 스키마 설계 [INFRA] - 5h

**산출물**:
```sql
-- 핵심 테이블
CREATE TABLE tick_data (...);       -- 틱데이터
CREATE TABLE stock_master (...);    -- 종목 마스터
CREATE TABLE orders (...);          -- 주문 내역
CREATE TABLE us_sector_data (...);  -- 미국 섹터
```

**완료 조건**:
- [ ] 모든 테이블 생성 스크립트
- [ ] 파티셔닝 설정
- [ ] 인덱스 설정

**의존성**: TASK-000

---

### TASK-003: Redis 캐시 서버 [INFRA] - 1h

**설정**:
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

**완료 조건**:
- [ ] Redis 컨테이너 기동
- [ ] 연결 테스트

**의존성**: TASK-000

---

## Phase 1: Sub Server 우선 구축 (2주) ⭐

> **총 시간**: 60시간 (기존 70h → 10h 단축!)  
> **목표**: REST API로 틱데이터 수집 시스템 구축

### 전략: REST API가 더 간단합니다!

**COM 방식의 복잡성**:
- Windows 환경 필수
- 복잡한 이벤트 핸들링
- 디버깅 어려움

**REST API의 단순함**:
- HTTP 요청/응답
- WebSocket으로 실시간
- 디버깅 쉬움

---

### TASK-100: 키움 REST API 클라이언트 [BE] - 8h

**목적**: REST API 래퍼 클래스 구현

**산출물**:
```python
# /backend/kiwoom/rest_client.py

import requests
from typing import Optional

class KiwoomRESTClient:
    """키움증권 REST API 클라이언트"""
    
    def __init__(self, appkey: str, secretkey: str, is_mock: bool = False):
        self.appkey = appkey
        self.secretkey = secretkey
        self.base_url = "https://mockapi.kiwoom.com" if is_mock else "https://api.kiwoom.com"
        self.token = None
    
    def get_token(self) -> str:
        """OAuth 토큰 발급"""
        url = f"{self.base_url}/oauth2/token"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "secretkey": self.secretkey
        }
        response = requests.post(url, json=body)
        data = response.json()
        self.token = data['token']
        return self.token
    
    def get_stock_price(self, stock_code: str) -> dict:
        """주식 현재가 조회 (ka10001)"""
        url = f"{self.base_url}/api/dostk/stkinfo"
        headers = {"authorization": f"Bearer {self.token}"}
        body = {"stk_cd": stock_code, "dmst_stex_tp": "KRX"}
        
        response = requests.post(url, headers=headers, json=body)
        return response.json()
    
    def buy_stock(self, stock_code: str, quantity: int, price: int = 0) -> dict:
        """주식 매수 (kt10000)"""
        url = f"{self.base_url}/api/dostk/ordr"
        headers = {"authorization": f"Bearer {self.token}"}
        body = {
            "dmst_stex_tp": "KRX",
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": "3" if price == 0 else "0"  # 3:시장가, 0:지정가
        }
        
        response = requests.post(url, headers=headers, json=body)
        return response.json()
```

**완료 조건**:
- [ ] OAuth 토큰 발급
- [ ] 현재가 조회
- [ ] 주문 실행 (매수/매도)
- [ ] 주문 정정/취소
- [ ] 단위 테스트

**예상 시간**: 8시간  
**의존성**: TASK-001  
**우선순위**: P0

---

### TASK-101: WebSocket 클라이언트 [BE] - 8h

**목적**: 실시간 데이터 수신

**산출물**:
```python
# /backend/kiwoom/websocket_client.py

import websocket
import json
import threading

class KiwoomWebSocket:
    """키움 REST API WebSocket 클라이언트"""
    
    def __init__(self, token: str, is_mock: bool = False):
        self.token = token
        base = "wss://mockapi.kiwoom.com:10000" if is_mock else "wss://api.kiwoom.com:10000"
        self.url = f"{base}/api/dostk/websocket"
        self.ws = None
        self.callbacks = {}
    
    def connect(self):
        """WebSocket 연결"""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        thread = threading.Thread(target=self.ws.run_forever)
        thread.daemon = True
        thread.start()
    
    def subscribe_tick(self, stock_codes: list, callback):
        """실시간 체결 구독 (0B)"""
        for code in stock_codes:
            self.callbacks[f"0B:{code}"] = callback
        
        message = {
            "header": {
                "api-id": "0B",
                "authorization": f"Bearer {self.token}"
            },
            "body": {
                "trnm": "REG",
                "grp_no": "0001",
                "refresh": "1",
                "data": [
                    {"item": f"KRX:{code}", "type": "0B"}
                    for code in stock_codes
                ]
            }
        }
        
        self.ws.send(json.dumps(message))
    
    def _on_message(self, ws, message):
        """실시간 데이터 수신"""
        data = json.loads(message)
        
        if data.get('body', {}).get('trnm') == 'REAL':
            for item in data['body']['data']:
                stock_code = item['item']
                values = item['values']
                
                # 콜백 실행
                key = f"0B:{stock_code}"
                if key in self.callbacks:
                    tick_data = {
                        'stock_code': stock_code,
                        'time': values.get('20'),      # 체결시간
                        'price': int(values.get('10')), # 현재가
                        'volume': int(values.get('15')), # 거래량
                        'strength': values.get('13')    # 등락율
                    }
                    self.callbacks[key](tick_data)
```

**완료 조건**:
- [ ] WebSocket 연결
- [ ] 실시간 체결 구독 (0B)
- [ ] 실시간 호가 구독 (0D)
- [ ] 콜백 방식 데이터 전달
- [ ] 재연결 로직

**예상 시간**: 8시간  
**의존성**: TASK-100  
**우선순위**: P0

---

### TASK-300: Sub Server 프로젝트 초기화 [INFRA] - 3h

**산출물**:
```
/sub-server
  /api
    - rest_client.py       # TASK-100
    - websocket_client.py  # TASK-101
  /collectors
    - tick_collector.py
  /models
    - tick_data.py
  /services
    - storage_service.py
  main.py
  requirements.txt
```

**requirements.txt**:
```
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
websocket-client==1.6.4
sqlalchemy==2.0.23
pymysql==1.1.0
redis==5.0.1
```

**완료 조건**:
- [ ] 프로젝트 구조
- [ ] Docker 설정
- [ ] DB 연결 테스트

**예상 시간**: 3시간  
**의존성**: TASK-000

---

### TASK-301: 틱데이터 수집 엔진 [BE] - 10h ⭐

**목적**: WebSocket으로 틱 수신 → DB 저장

**산출물**:
```python
# /sub-server/collectors/tick_collector.py

from api.websocket_client import KiwoomWebSocket
from services.storage_service import TickStorageService
import time

class TickCollector:
    """틱데이터 수집기"""
    
    def __init__(self, token: str, is_mock: bool = False):
        self.ws_client = KiwoomWebSocket(token, is_mock)
        self.storage = TickStorageService()
        self.buffer = []
        self.buffer_size = 10000
    
    def start(self, stock_codes: list):
        """수집 시작"""
        print(f"수집 시작: {len(stock_codes)}개 종목")
        
        # WebSocket 연결
        self.ws_client.connect()
        time.sleep(2)  # 연결 대기
        
        # 실시간 체결 구독
        self.ws_client.subscribe_tick(stock_codes, self.on_tick_received)
        
        print("WebSocket 구독 완료")
    
    def on_tick_received(self, tick_data: dict):
        """틱 수신 콜백"""
        self.buffer.append(tick_data)
        
        # 버퍼 가득 차면 저장
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self):
        """버퍼 → DB 저장"""
        if not self.buffer:
            return
        
        print(f"DB 저장: {len(self.buffer)}건")
        self.storage.bulk_insert(self.buffer)
        self.buffer.clear()
    
    def stop(self):
        """수집 중지"""
        self.flush()  # 남은 버퍼 저장
        print("수집 중지")

# 사용 예시
if __name__ == "__main__":
    from api.rest_client import KiwoomRESTClient
    
    # 토큰 발급
    client = KiwoomRESTClient(appkey="...", secretkey="...", is_mock=True)
    token = client.get_token()
    
    # 수집 시작
    collector = TickCollector(token, is_mock=True)
    collector.start(stock_codes=["005930", "000660", "035420"])
    
    # 6시간 수집 (장 시간)
    try:
        time.sleep(6 * 3600)
    except KeyboardInterrupt:
        collector.stop()
```

**완료 조건**:
- [ ] WebSocket 실시간 틱 수신
- [ ] 10,000건 버퍼링
- [ ] DB 일괄 저장
- [ ] 10종목 이상 동시 수집
- [ ] 에러 시 재연결

**예상 시간**: 10시간  
**의존성**: TASK-101, TASK-300, TASK-002  
**우선순위**: P0

---

### TASK-302: DB 최적화 [INFRA] - 6h

(기존과 동일 - 생략)

**예상 시간**: 6시간

---

### TASK-303: 수집 대상 종목 관리 [BE] - 4h

(기존과 동일 - 생략)

**예상 시간**: 4시간

---

### TASK-304: 틱데이터 조회 API [BE] - 4h

**산출물**:
```python
# /sub-server/main.py

from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/api/tick-data/{stock_code}")
async def get_tick_data(
    stock_code: str,
    start_time: datetime,
    end_time: datetime,
    limit: int = 1000
):
    """틱데이터 조회"""
    # DB에서 조회
    ticks = storage.query(stock_code, start_time, end_time, limit)
    return {"data": ticks}

@app.get("/api/status")
async def get_status():
    """서버 상태"""
    return {
        "uptime": get_uptime(),
        "tick_count_today": get_tick_count_today(),
        "db_size": get_db_size(),
        "collecting_stocks": get_collecting_stocks()
    }
```

**예상 시간**: 4시간

---

### TASK-305: 모니터링 대시보드 [FE] - 5h

**산출물**:
```html
<!-- /sub-server/static/dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Sub Server 모니터링</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>🚀 Sub Server 실시간 모니터링</h1>
    
    <div class="stats">
        <div class="stat-card">
            <h3>가동 시간</h3>
            <p id="uptime">-</p>
        </div>
        <div class="stat-card">
            <h3>오늘 수집 틱 수</h3>
            <p id="tick-count">-</p>
        </div>
        <div class="stat-card">
            <h3>DB 용량</h3>
            <p id="db-size">-</p>
        </div>
    </div>
    
    <canvas id="tick-chart"></canvas>
    
    <script>
        // 5초마다 상태 갱신
        setInterval(async () => {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            document.getElementById('uptime').textContent = data.uptime;
            document.getElementById('tick-count').textContent = data.tick_count_today.toLocaleString();
            document.getElementById('db-size').textContent = data.db_size;
        }, 5000);
    </script>
</body>
</html>
```

**예상 시간**: 5시간

---

### TASK-306: 자동 시작/중지 [BE] - 3h

(기존과 동일 - 생략)

**예상 시간**: 3시간

---

### TASK-307: 데이터 아카이빙 [BE] - 6h

(기존과 동일 - 생략)

**예상 시간**: 6시간

---

### TASK-308: Sub Server 통합 테스트 [QA] - 11h

**테스트 시나리오**:
1. **REST API 테스트**
   - 토큰 발급 성공
   - 현재가 조회 성공
   - 주문 실행 성공

2. **WebSocket 테스트**
   - 연결 성공
   - 실시간 틱 수신 (10초 내 100건 이상)
   - 재연결 동작 확인

3. **수집 엔진 테스트**
   - 10종목 동시 수집
   - 버퍼링 및 DB 저장 확인

4. **24시간 안정성 테스트**
   - 메모리 누수 체크
   - 에러 로그 검토

**완료 조건**:
- [ ] 모든 시나리오 PASS
- [ ] 24시간 안정 가동
- [ ] 하루 500만 건 이상 수집

**예상 시간**: 11시간  
**의존성**: TASK-300~307

---

## Phase 1 완료 후 상태

### ✅ REST API 기반 Sub Server 가동!

**특징**:
- ✅ 크로스 플랫폼 (Linux 서버 가능)
- ✅ OAuth 토큰 자동 갱신 (24시간마다)
- ✅ WebSocket 실시간 틱 수신
- ✅ 거래대금 TOP 50 종목 수집
- ✅ 하루 500만~1,000만 건 저장

**데이터 축적**:
- 2주 후: 5천만 건
- 1개월 후: 2억 건
- 3개월 후: 6억 건 ← 백테스팅!

---

## Phase 2: Main Server MVP (4주)

> **총 시간**: 100시간 (기존 114h → 14h 단축!)

### 백엔드 (40h)

#### TASK-110: Main Backend 초기화 [BE] - 3h
- FastAPI 프로젝트 생성
- TASK-100, 101 코드 재사용

#### TASK-111: 주문 API [BE] - 8h
```python
@app.post("/api/orders")
async def create_order(order: OrderRequest):
    """주문 실행"""
    result = kiwoom_client.buy_stock(
        stock_code=order.stock_code,
        quantity=order.quantity,
        price=order.price
    )
    return result
```

#### TASK-112: 주문 조회 API [BE] - 4h
#### TASK-113: 실시간 호가 WebSocket [BE] - 6h
#### TASK-114: 호가 데이터 API [BE] - 5h
#### TASK-115: 종목 검색 API [BE] - 4h
#### TASK-116: 차트 데이터 API [BE] - 6h
- Sub Server 틱데이터 활용
- 분봉/일봉 집계

### 프론트엔드 (40h)

#### TASK-120: Next.js 초기 설정 [FE] - 3h
#### TASK-121: 로그인 페이지 [FE] - 2h
- OAuth 토큰 발급 UI

#### TASK-122: 대시보드 레이아웃 [FE] - 5h
#### TASK-123: 종목 검색 [FE] - 4h
#### TASK-124: 실시간 호가창 [FE] - 8h
- WebSocket 연결

#### TASK-125: 주문 패널 [FE] - 6h
#### TASK-126: 미체결 주문 [FE] - 5h
#### TASK-127: TradingView 차트 [FE] - 10h

### 풀스택 (8h)

#### TASK-128: 차트 실시간 업데이트 [FS] - 8h

### QA (6h)

#### TASK-129: MVP 통합 테스트 [QA] - 6h

---

## Phase 3: 섹터 연동 (3주)

> **총 시간**: 38시간 (동일)

(기존과 동일 - 생략)

---

## Phase 4: 프리미엄 (진행 중)

> **총 시간**: 26시간 (동일)

(기존과 동일 - 생략)

---

## 전체 요약

### 시간 통계

| Phase | 시간 | 변경 | 주요 목표 |
|-------|------|------|-----------|
| Phase 0 | 12h | **-3h** | App Key 발급 |
| Phase 1 | 60h | **-10h** | Sub Server (REST API) |
| Phase 2 | 100h | **-14h** | Main Server |
| Phase 3 | 38h | 동일 | 섹터 연동 |
| Phase 4 | 26h | 동일 | 프리미엄 |
| **총합** | **236h** | **-27h** | **약 6주** |

### REST API vs COM API 비교

| 항목 | COM API | REST API |
|------|---------|----------|
| OS | Windows만 | 크로스 플랫폼 ✅ |
| 복잡도 | 높음 | 낮음 ✅ |
| 디버깅 | 어려움 | 쉬움 ✅ |
| 브라우저 | 불가 | 가능 ✅ |
| 배포 | 복잡 | 간단 ✅ |
| 개발 시간 | 240h | 236h ✅ |

---

## Critical Path

```
Day 1: TASK-000 (환경) + TASK-001 (App Key 발급)
       ↓
Day 2-3: TASK-002, 003 (DB + Redis)
       ↓
Day 4-5: TASK-100 (REST 클라이언트) ⭐
       ↓
Week 2: TASK-101 (WebSocket) + TASK-301 (틱 수집) ⭐⭐
       ↓
Week 3: TASK-302~308 (최적화 + 테스트)
       ↓
[Sub Server 가동!]
       ↓
Week 4-7: Main Server 개발
```

---

## 즉시 시작

### 오늘 할 일
- [ ] TASK-000: Git 저장소 생성
- [ ] TASK-001: 키움증권 REST API 신청
  - 홈페이지 → REST API 메뉴
  - App Key/Secret Key 발급

### 이번 주 목표
- [ ] Phase 0 완료
- [ ] TASK-100: REST 클라이언트 완성
- [ ] OAuth 토큰 발급 테스트 성공

### 다음 주 목표
- [ ] TASK-101: WebSocket 클라이언트
- [ ] TASK-301: 틱 수집 엔진 ⭐
- [ ] 첫 틱데이터 수집 성공!

---

## 부록: REST API 빠른 시작

### 1분 만에 테스트하기

```python
import requests

# 1. 토큰 발급
url = "https://mockapi.kiwoom.com/oauth2/token"
body = {
    "grant_type": "client_credentials",
    "appkey": "YOUR_APP_KEY",
    "secretkey": "YOUR_SECRET_KEY"
}
res = requests.post(url, json=body)
token = res.json()['token']

# 2. 삼성전자 현재가 조회
url = "https://mockapi.kiwoom.com/api/dostk/stkinfo"
headers = {"authorization": f"Bearer {token}"}
body = {"stk_cd": "005930", "dmst_stex_tp": "KRX"}
res = requests.post(url, headers=headers, json=body)
print(res.json())

# 완료! 이게 전부입니다 🎉
```

---

**문서 버전**: 3.0 (REST API + Sub Server 우선)  
**최종 수정일**: 2025-11-15  
**작성자**: Claude  

**🚀 REST API로 더 빠르고 간단하게!**
