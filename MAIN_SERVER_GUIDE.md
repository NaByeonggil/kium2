# Main Server 가이드

## 개요

Main Server는 사용자 트레이딩 인터페이스를 제공하는 서버입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Server (포트 8000)                  │
├─────────────────────────────────────────────────────────────┤
│  📈 매매 주문 (매수/매도/정정/취소)                          │
│  📊 호가창 (10호가)                                         │
│  🔍 종목 검색 + 차트                                        │
│  💰 잔고/포트폴리오                                         │
│  🇺🇸 US ETF 섹터 데이터                                    │
│  🔗 Sub Server 연동                                         │
│  ⚡ WebSocket 실시간 스트림                                 │
└─────────────────────────────────────────────────────────────┘
```

## 아키텍처

```
                    ┌──────────────────┐
                    │   Frontend       │
                    │   (React)        │
                    └────────┬─────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│                   Main Server (:8000)                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                 │  │
│  │                                                      │  │
│  │  /api/orderbook   → 10호가 조회                      │  │
│  │  /api/trading     → 매수/매도/정정/취소              │  │
│  │  /api/balance     → 잔고/포트폴리오                  │  │
│  │  /api/stocks      → 종목 검색/현재가/차트            │  │
│  │  /api/us-market   → US ETF 섹터                      │  │
│  │  /api/sub-server  → Sub Server 연동                  │  │
│  │  /ws              → WebSocket 실시간                 │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────┬───────────────────────────┬───────────────┘
                 │                           │
                 ▼                           ▼
        ┌────────────────┐          ┌────────────────┐
        │  Kiwoom API    │          │  Sub Server    │
        │  (실시간 매매)  │          │  (:8001)       │
        └────────────────┘          └────────────────┘
```

## 빠른 시작

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정 (.env)

```env
# 키움 API
KIWOOM_APP_KEY=your_app_key
KIWOOM_SECRET_KEY=your_secret_key
KIWOOM_IS_MOCK=true

# Main Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Sub Server
SUB_SERVER_URL=http://localhost:8001

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 3. 서버 실행

```bash
# 방법 1: Python 직접 실행
python main_server/main.py

# 방법 2: uvicorn 실행
uvicorn main_server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 엔드포인트

### 호가창 (Orderbook)

```bash
# 10호가 조회
GET /api/orderbook/{stock_code}

# 호가 요약
GET /api/orderbook/{stock_code}/summary
```

### 매매 (Trading)

```bash
# 주문 실행
POST /api/trading/order
{
    "stock_code": "005930",
    "side": "buy",
    "quantity": 10,
    "price": 72500,
    "order_type": "0"
}

# 매수 (간편)
POST /api/trading/buy?stock_code=005930&quantity=10&price=72500

# 매도 (간편)
POST /api/trading/sell?stock_code=005930&quantity=10&price=72500

# 주문 정정
PUT /api/trading/modify
{
    "order_no": "0001234",
    "stock_code": "005930",
    "quantity": 5,
    "price": 72000
}

# 주문 취소
DELETE /api/trading/cancel
{
    "order_no": "0001234",
    "stock_code": "005930",
    "quantity": 10
}

# 미체결 주문 조회
GET /api/trading/open-orders
```

### 잔고 (Balance)

```bash
# 계좌 잔고 전체
GET /api/balance

# 잔고 요약
GET /api/balance/summary

# 보유 종목만
GET /api/balance/holdings

# 특정 종목 보유 상세
GET /api/balance/holding/{stock_code}
```

### 종목 (Stocks)

```bash
# 종목 검색
GET /api/stocks/search?keyword=삼성&limit=20

# 현재가 조회
GET /api/stocks/{stock_code}

# 일봉 차트
GET /api/stocks/{stock_code}/chart/daily?days=60

# 분봉 차트
GET /api/stocks/{stock_code}/chart/minute?interval=1

# 거래대금 상위
GET /api/stocks/ranking/top-trading?market=0&limit=50

# 종목 종합 정보 (현재가 + 호가 + 4등분라인)
GET /api/stocks/{stock_code}/info
```

### US Market

```bash
# 모든 섹터
GET /api/us-market/sectors

# 섹터 성과 (상승/하락 순위)
GET /api/us-market/sectors/performance

# 추천 섹터 (상위 3개)
GET /api/us-market/sectors/recommended

# 단일 ETF
GET /api/us-market/etf/{symbol}

# 섹터 + 한국 관련 종목
GET /api/us-market/sector/{sector_name}

# US-KR 섹터 매핑
GET /api/us-market/mapping
```

### Sub Server 연동

```bash
# Sub Server 상태
GET /api/sub-server/status

# 헬스 체크
GET /api/sub-server/health

# 수집기 통계
GET /api/sub-server/collector

# 데이터베이스 통계
GET /api/sub-server/database

# 수집 중인 종목
GET /api/sub-server/stocks

# 종목 추가
POST /api/sub-server/stocks/add?stock_code=005930

# 종목 제거
POST /api/sub-server/stocks/remove?stock_code=005930
```

### WebSocket

```javascript
// 일반 WebSocket 연결
const ws = new WebSocket('ws://localhost:8000/ws');

// 종목 구독
ws.send(JSON.stringify({
    action: 'subscribe',
    stock_code: '005930'
}));

// 구독 해제
ws.send(JSON.stringify({
    action: 'unsubscribe',
    stock_code: '005930'
}));

// 실시간 가격 스트림 (1초 간격)
const priceWs = new WebSocket('ws://localhost:8000/ws/price/005930');

// 실시간 호가 스트림 (500ms 간격)
const orderbookWs = new WebSocket('ws://localhost:8000/ws/orderbook/005930');
```

## 디렉토리 구조

```
main_server/
├── __init__.py
├── main.py                 # 엔트리포인트
├── api/
│   ├── __init__.py
│   └── kiwoom_trading_client.py  # 키움 API 클라이언트
├── config/
│   ├── __init__.py
│   └── settings.py         # 설정
├── models/
│   ├── __init__.py
│   └── schemas.py          # Pydantic 스키마
├── routes/
│   ├── __init__.py
│   ├── orderbook.py        # 호가창 API
│   ├── trading.py          # 매매 API
│   ├── balance.py          # 잔고 API
│   ├── stocks.py           # 종목 API
│   ├── us_market.py        # US Market API
│   ├── sub_server.py       # Sub Server 연동
│   └── websocket.py        # WebSocket
└── services/
    ├── __init__.py
    ├── us_market_service.py    # US Market 서비스
    └── sub_server_client.py    # Sub Server 클라이언트
```

## Sub Server와의 관계

| 기능 | Main Server | Sub Server |
|------|-------------|------------|
| **포트** | 8000 | 8001 |
| **역할** | 사용자 서비스 | 데이터 수집 |
| **키움 API** | 호가, 주문, 잔고 | 틱데이터, 랭킹 |
| **상태** | Phase 2 (신규) | Phase 1 (완료) |
| **데이터** | 읽기 + 쓰기 | 쓰기 전용 |

## 다음 단계

1. **Frontend 개발**
   - React + TradingView 차트
   - 호가창 UI
   - 매매 패널

2. **인증 추가**
   - JWT 토큰
   - 세션 관리

3. **고급 기능**
   - 알림 시스템
   - 자동매매 조건
   - 백테스팅 연동
