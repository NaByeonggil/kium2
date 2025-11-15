# 키움증권 REST API 완전 가이드

> 키움증권 REST API 공식 문서 해석 및 구현 가이드
> 
> 작성일: 2025년 10월 20일

---

## 📋 목차

1. [API 개요](#api-개요)
2. [기본 정보](#기본-정보)
3. [인증 (OAuth 2.0)](#인증-oauth-20)
4. [주요 API 카테고리](#주요-api-카테고리)
5. [실시간 데이터 (WebSocket)](#실시간-데이터-websocket)
6. [코드 구현 예제](#코드-구현-예제)
7. [에러 처리](#에러-처리)

---

## API 개요

### 📌 기본 사양

| 항목 | 내용 |
|------|------|
| **API 방식** | RESTful API + WebSocket |
| **인증 방식** | OAuth 2.0 (Client Credentials) |
| **데이터 형식** | JSON |
| **문자 인코딩** | UTF-8 |
| **토큰 유효기간** | 24시간 |
| **지원 OS** | Windows, macOS, Linux |
| **지원 언어** | Python, Java, JavaScript, 기타 모든 HTTP 클라이언트 |

---

## 기본 정보

### 🌐 도메인 URL

```
운영 환경 (실제 거래)
- REST API: https://api.kiwoom.com
- WebSocket: wss://api.kiwoom.com:10000

모의투자 환경 (테스트)
- REST API: https://mockapi.kiwoom.com
- WebSocket: wss://mockapi.kiwoom.com:10000
```

### 📊 전체 API 개수

- **총 207개 API** 제공
- REST API: 199개
- WebSocket 실시간: 18개

### 🔑 API 신청 방법

1. **키움증권 계좌 개설** (필수)
2. **홈페이지 접속**
   - 경로 1: 트레이딩 채널 → 키움 REST API
   - 경로 2: 고객서비스 → 다운로드 → Open API → 키움 REST API
3. **IP 주소 등록** (최대 10개)
4. **App Key / Secret Key 발급**
   - 실제 투자: 계좌 App Key 관리
   - 모의 투자: 모의투자 App Key 관리

---

## 인증 (OAuth 2.0)

### 1. 접근 토큰 발급

#### API 정보

| 항목 | 값 |
|------|-----|
| **API ID** | `au10001` |
| **Method** | `POST` |
| **URL** | `/oauth2/token` |
| **Content-Type** | `application/json;charset=UTF-8` |

#### 전체 URL

```
운영: https://api.kiwoom.com/oauth2/token
모의: https://mockapi.kiwoom.com/oauth2/token
```

#### Request Body

```json
{
  "grant_type": "client_credentials",
  "appkey": "Your_App_Key_Here",
  "secretkey": "Your_Secret_Key_Here"
}
```

#### Response

```json
{
  "expires_dt": "20241107083713",
  "token_type": "bearer",
  "token": "WQJCwyqInphKnR3bSRtB9NE1lv...",
  "return_code": 0,
  "return_msg": "정상적으로 처리되었습니다"
}
```

#### Python 구현 예제

```python
import requests

def get_access_token(appkey: str, secretkey: str, is_mock: bool = False):
    """
    키움증권 REST API 접근 토큰 발급
    
    Args:
        appkey: 발급받은 App Key
        secretkey: 발급받은 Secret Key
        is_mock: True일 경우 모의투자 환경
    
    Returns:
        dict: 토큰 정보 (token, expires_dt, token_type)
    """
    base_url = "https://mockapi.kiwoom.com" if is_mock else "https://api.kiwoom.com"
    url = f"{base_url}/oauth2/token"
    
    headers = {
        "Content-Type": "application/json;charset=UTF-8"
    }
    
    body = {
        "grant_type": "client_credentials",
        "appkey": appkey,
        "secretkey": secretkey
    }
    
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('return_code') == 0:
            return {
                'token': data['token'],
                'expires_dt': data['expires_dt'],
                'token_type': data['token_type']
            }
        else:
            raise Exception(f"Token Error: {data.get('return_msg')}")
    else:
        raise Exception(f"HTTP Error: {response.status_code}")

# 사용 예시
token_info = get_access_token(
    appkey="YOUR_APP_KEY",
    secretkey="YOUR_SECRET_KEY",
    is_mock=True  # 모의투자 환경
)

print(f"Access Token: {token_info['token']}")
print(f"Expires: {token_info['expires_dt']}")
```

### 2. 접근 토큰 폐기

#### API 정보

| 항목 | 값 |
|------|-----|
| **API ID** | `au10002` |
| **Method** | `POST` |
| **URL** | `/oauth2/revoke` |

#### Request Body

```json
{
  "appkey": "Your_App_Key_Here",
  "secretkey": "Your_Secret_Key_Here",
  "token": "WQJCwyqInphKnR3bSRtB9NE1lv..."
}
```

---

## 주요 API 카테고리

### 📈 1. 계좌 정보 조회

#### 계좌평가잔고내역요청 (kt00018)

**목적**: 보유 종목 및 계좌 평가 정보 조회

| 항목 | 값 |
|------|-----|
| **API ID** | `kt00018` |
| **Method** | `POST` |
| **URL** | `/api/dostk/acnt` |

**Request Headers**

```json
{
  "api-id": "kt00018",
  "authorization": "Bearer {access_token}",
  "Content-Type": "application/json;charset=UTF-8"
}
```

**Request Body**

```json
{
  "qry_tp": "1",           // 1:합산, 2:개별
  "dmst_stex_tp": "KRX"    // KRX:한국거래소, NXT:넥스트트레이드
}
```

**Response Body (주요 필드)**

```json
{
  "return_code": 0,
  "return_msg": "정상적으로 처리되었습니다",
  "tot_pur_amt": "10000000",      // 총매입금액
  "tot_evlt_amt": "11500000",     // 총평가금액
  "tot_evlt_pl": "1500000",       // 총평가손익
  "tot_evlt_pl_rate": "15.00",    // 총평가손익률
  "data": [
    {
      "stk_cd": "005930",         // 종목코드
      "stk_nm": "삼성전자",        // 종목명
      "ord_psbqty": "10",         // 주문가능수량
      "hld_qty": "10",            // 보유수량
      "ord_uv": "70000",          // 매입단가
      "now_uv": "75000",          // 현재가
      "evlt_pl": "50000",         // 평가손익
      "evlt_pl_rate": "7.14"      // 평가손익률
    }
  ]
}
```

**Python 구현**

```python
def get_account_balance(token: str, qry_tp: str = "1", is_mock: bool = False):
    """
    계좌 평가 잔고 조회
    
    Args:
        token: 접근 토큰
        qry_tp: 조회구분 (1:합산, 2:개별)
        is_mock: 모의투자 여부
    """
    base_url = "https://mockapi.kiwoom.com" if is_mock else "https://api.kiwoom.com"
    url = f"{base_url}/api/dostk/acnt"
    
    headers = {
        "api-id": "kt00018",
        "authorization": f"Bearer {token}",
        "Content-Type": "application/json;charset=UTF-8"
    }
    
    body = {
        "qry_tp": qry_tp,
        "dmst_stex_tp": "KRX"
    }
    
    response = requests.post(url, headers=headers, json=body)
    return response.json()
```

#### 미체결요청 (ka10075)

**목적**: 체결되지 않은 주문 내역 조회

| 항목 | 값 |
|------|-----|
| **API ID** | `ka10075` |
| **URL** | `/api/dostk/acnt` |

**Request Body**

```json
{
  "stk_cd": "",              // 종목코드 (전체 조회시 빈값)
  "dmst_stex_tp": "KRX"
}
```

#### 체결요청 (ka10076)

**목적**: 체결된 주문 내역 조회

### 💰 2. 주문 (매매)

#### 주식 매수 주문 (kt10000)

| 항목 | 값 |
|------|-----|
| **API ID** | `kt10000` |
| **Method** | `POST` |
| **URL** | `/api/dostk/ordr` |

**Request Headers**

```json
{
  "api-id": "kt10000",
  "authorization": "Bearer {access_token}",
  "Content-Type": "application/json;charset=UTF-8"
}
```

**Request Body**

```json
{
  "dmst_stex_tp": "KRX",     // 거래소구분: KRX, NXT, SOR
  "stk_cd": "005930",        // 종목코드
  "ord_qty": "10",           // 주문수량
  "ord_uv": "75000",         // 주문단가 (시장가는 빈값)
  "trde_tp": "0",            // 매매구분 (아래 참조)
  "cond_uv": ""              // 조건단가 (조건부 주문시)
}
```

**매매구분 (trde_tp) 코드**

| 코드 | 설명 |
|-----|------|
| `0` | 보통 (지정가) |
| `3` | 시장가 |
| `5` | 조건부지정가 |
| `6` | 최유리지정가 |
| `7` | 최우선지정가 |
| `10` | 보통(IOC) |
| `13` | 시장가(IOC) |
| `16` | 최유리(IOC) |
| `20` | 보통(FOK) |
| `23` | 시장가(FOK) |
| `26` | 최유리(FOK) |
| `28` | 스톱지정가 |
| `29` | 중간가 |
| `30` | 중간가(IOC) |
| `31` | 중간가(FOK) |
| `61` | 장시작전시간외 |
| `62` | 시간외단일가 |
| `81` | 장마감후시간외 |

**Response**

```json
{
  "ord_no": "00024",        // 주문번호
  "dmst_stex_tp": "KRX",
  "return_code": 0,
  "return_msg": "정상적으로 처리되었습니다"
}
```

**Python 구현**

```python
def buy_stock(
    token: str,
    stock_code: str,
    quantity: int,
    price: int = 0,
    order_type: str = "3",
    exchange: str = "KRX",
    is_mock: bool = False
):
    """
    주식 매수 주문
    
    Args:
        token: 접근 토큰
        stock_code: 종목코드 (예: "005930")
        quantity: 주문수량
        price: 주문가격 (시장가일 경우 0)
        order_type: 매매구분 (0:지정가, 3:시장가)
        exchange: 거래소 (KRX, NXT, SOR)
        is_mock: 모의투자 여부
    
    Returns:
        dict: 주문 결과 (ord_no 포함)
    """
    base_url = "https://mockapi.kiwoom.com" if is_mock else "https://api.kiwoom.com"
    url = f"{base_url}/api/dostk/ordr"
    
    headers = {
        "api-id": "kt10000",
        "authorization": f"Bearer {token}",
        "Content-Type": "application/json;charset=UTF-8"
    }
    
    body = {
        "dmst_stex_tp": exchange,
        "stk_cd": stock_code,
        "ord_qty": str(quantity),
        "ord_uv": str(price) if price > 0 else "",
        "trde_tp": order_type,
        "cond_uv": ""
    }
    
    response = requests.post(url, headers=headers, json=body)
    return response.json()

# 사용 예시 - 삼성전자 시장가 10주 매수
result = buy_stock(
    token=access_token,
    stock_code="005930",
    quantity=10,
    order_type="3",  # 시장가
    is_mock=True
)
print(f"주문번호: {result['ord_no']}")
```

#### 주식 매도 주문 (kt10001)

| 항목 | 값 |
|------|-----|
| **API ID** | `kt10001` |
| **URL** | `/api/dostk/ordr` |

**Request Body** (매수와 동일한 구조)

#### 주식 정정 주문 (kt10002)

**목적**: 미체결 주문의 가격/수량 변경

**Request Body**

```json
{
  "dmst_stex_tp": "KRX",
  "org_ord_no": "00024",     // 원주문번호
  "stk_cd": "005930",
  "ord_qty": "10",           // 정정할 수량
  "ord_uv": "76000",         // 정정할 가격
  "trde_tp": "0"
}
```

#### 주식 취소 주문 (kt10003)

**목적**: 미체결 주문 취소

**Request Body**

```json
{
  "dmst_stex_tp": "KRX",
  "org_ord_no": "00024",     // 원주문번호
  "stk_cd": "005930",
  "ord_qty": "10"            // 취소할 수량
}
```

### 📊 3. 시세 조회

#### 주식 현재가 조회 (ka10001)

| 항목 | 값 |
|------|-----|
| **API ID** | `ka10001` |
| **URL** | `/api/dostk/stkinfo` |

**Request Body**

```json
{
  "stk_cd": "005930",
  "dmst_stex_tp": "KRX"
}
```

**Response (주요 필드)**

```json
{
  "stk_cd": "005930",
  "stk_nm": "삼성전자",
  "now_uv": "75000",         // 현재가
  "prdy_vrss": "1000",       // 전일대비
  "prdy_vrss_sign": "2",     // 전일대비부호 (2:상승, 5:하락)
  "prdy_ctrt": "1.35",       // 전일대비율
  "acml_vol": "15234567",    // 누적거래량
  "acml_tr_pbmn": "1145678", // 누적거래대금(백만)
  "hgprc": "76000",          // 고가
  "lwprc": "74000",          // 저가
  "strt_uv": "74500"         // 시가
}
```

#### 주식호가요청 (ka10004)

**목적**: 실시간 호가 정보 조회

**Response (주요 필드)**

```json
{
  "stk_cd": "005930",
  "ofr_uv1": "75100",        // 매도호가1
  "bid_uv1": "75000",        // 매수호가1
  "ofr_qty1": "1234",        // 매도호가수량1
  "bid_qty1": "5678",        // 매수호가수량1
  // ... 10단계 호가
}
```

### 📈 4. 차트 데이터

#### 주식일봉차트조회요청 (ka10081)

| 항목 | 값 |
|------|-----|
| **API ID** | `ka10081` |
| **URL** | `/api/dostk/chart` |

**Request Body**

```json
{
  "stk_cd": "005930",
  "dmst_stex_tp": "KRX",
  "inqr_strt_dt": "20240101",  // 조회시작일
  "inqr_end_dt": "20241020"    // 조회종료일
}
```

**Response**

```json
{
  "data": [
    {
      "stck_bsop_date": "20241020",  // 영업일자
      "stck_oprc": "74500",          // 시가
      "stck_hgpr": "76000",          // 고가
      "stck_lwpr": "74000",          // 저가
      "stck_clpr": "75000",          // 종가
      "acml_vol": "15234567",        // 거래량
      "acml_tr_pbmn": "1145678"      // 거래대금
    }
  ]
}
```

#### 주식분봉차트조회요청 (ka10080)

**Request Body**

```json
{
  "stk_cd": "005930",
  "dmst_stex_tp": "KRX",
  "time_tp": "1",            // 시간구분: 1(1분), 3(3분), 5(5분), 10(10분), 30(30분), 60(60분)
  "inqr_strt_dt": "20241020",
  "inqr_end_dt": "20241020"
}
```

### 🔍 5. 종목 정보

#### 종목정보 리스트 (ka10099)

**목적**: 시장별 전체 종목 코드 조회

**Request Body**

```json
{
  "mkt_tp": "ALL"            // ALL:전체, KOSPI:코스피, KOSDAQ:코스닥, ETF, ETN
}
```

**Response**

```json
{
  "data": [
    {
      "stk_cd": "005930",
      "stk_nm": "삼성전자",
      "mkt_tp": "KOSPI"
    }
  ]
}
```

#### 종목정보 조회 (ka10100)

**목적**: 특정 종목의 상세 정보 조회

---

## 실시간 데이터 (WebSocket)

### 🔌 WebSocket 연결

#### 기본 정보

| 항목 | 값 |
|------|-----|
| **프로토콜** | WebSocket (wss://) |
| **운영 URL** | `wss://api.kiwoom.com:10000/api/dostk/websocket` |
| **모의 URL** | `wss://mockapi.kiwoom.com:10000/api/dostk/websocket` |
| **Format** | JSON |

### 📡 실시간 데이터 등록

#### Request 구조

```json
{
  "header": {
    "api-id": "0B",                    // 실시간 TR 코드
    "authorization": "Bearer {token}",
    "cont-yn": "N",
    "next-key": ""
  },
  "body": {
    "trnm": "REG",                     // REG:등록, REMOVE:해제
    "grp_no": "0001",                  // 그룹번호 (4자리)
    "refresh": "1",                    // 0:기존유지안함, 1:기존유지
    "data": [
      {
        "item": "KRX:005930",          // 거래소:종목코드
        "type": "0B"                   // 실시간 TR 코드
      },
      {
        "item": "KRX:000660",
        "type": "0B"
      }
    ]
  }
}
```

#### Response (실시간 데이터)

```json
{
  "header": {
    "api-id": "0B"
  },
  "body": {
    "return_code": 0,
    "return_msg": "정상",
    "trnm": "REAL",
    "data": [
      {
        "type": "0B",
        "name": "주식체결",
        "item": "005930",
        "values": {
          "20": "153045",              // 체결시간 (HHMMSS)
          "10": "75000",               // 현재가
          "11": "상승",                 // 전일대비구분
          "12": "1000",                // 전일대비
          "13": "1.35",                // 등락율
          "15": "120000",              // 거래량
          "16": "12345678"             // 누적거래량
        }
      }
    ]
  }
}
```

### 📊 주요 실시간 TR

#### 1. 주식체결 (0B)

**데이터 항목**

| 필드번호 | 필드명 | 설명 |
|---------|--------|------|
| `10` | 현재가 | 체결가 |
| `11` | 전일대비구분 | 상승/하락/보합 |
| `12` | 전일대비 | 전일대비 가격 |
| `13` | 등락율 | 전일대비율 |
| `15` | 거래량 | 체결량 |
| `16` | 누적거래량 | |
| `17` | 누적거래대금 | |
| `18` | 시가 | |
| `19` | 고가 | |
| `20` | 체결시간 | HHMMSS |
| `21` | 저가 | |

#### 2. 주식호가잔량 (0D)

**데이터 항목**

| 필드번호 | 필드명 |
|---------|--------|
| `51~60` | 매도호가1~10 |
| `61~70` | 매수호가1~10 |
| `71~80` | 매도호가수량1~10 |
| `81~90` | 매수호가수량1~10 |

#### 3. 주문체결 (00)

**목적**: 내 계좌의 주문/체결 실시간 알림

### Python WebSocket 구현

```python
import websocket
import json
import threading

class KiwoomWebSocket:
    def __init__(self, token: str, is_mock: bool = False):
        self.token = token
        base_url = "wss://mockapi.kiwoom.com:10000" if is_mock else "wss://api.kiwoom.com:10000"
        self.url = f"{base_url}/api/dostk/websocket"
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
        
        # 백그라운드 스레드에서 실행
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()
        
    def _on_open(self, ws):
        print("WebSocket 연결됨")
        
    def _on_message(self, ws, message):
        """실시간 데이터 수신"""
        data = json.loads(message)
        
        # trnm이 REAL일 때만 실시간 데이터
        if data.get('body', {}).get('trnm') == 'REAL':
            for item in data['body']['data']:
                tr_type = item['type']
                stock_code = item['item']
                values = item['values']
                
                # 콜백 실행
                callback_key = f"{tr_type}:{stock_code}"
                if callback_key in self.callbacks:
                    self.callbacks[callback_key](values)
        
    def _on_error(self, ws, error):
        print(f"WebSocket 에러: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket 연결 종료")
        
    def subscribe(self, stock_codes: list, tr_type: str = "0B", callback=None):
        """
        실시간 데이터 등록
        
        Args:
            stock_codes: 종목코드 리스트 (예: ["005930", "000660"])
            tr_type: 실시간 TR 코드 (0B:주식체결, 0D:호가잔량)
            callback: 데이터 수신 콜백 함수
        """
        # 콜백 등록
        for code in stock_codes:
            callback_key = f"{tr_type}:{code}"
            if callback:
                self.callbacks[callback_key] = callback
        
        # 등록 메시지 전송
        data_list = [
            {"item": f"KRX:{code}", "type": tr_type}
            for code in stock_codes
        ]
        
        message = {
            "header": {
                "api-id": tr_type,
                "authorization": f"Bearer {self.token}",
                "cont-yn": "N",
                "next-key": ""
            },
            "body": {
                "trnm": "REG",
                "grp_no": "0001",
                "refresh": "1",
                "data": data_list
            }
        }
        
        self.ws.send(json.dumps(message))
        
    def unsubscribe(self, stock_codes: list, tr_type: str = "0B"):
        """실시간 데이터 해제"""
        data_list = [
            {"item": f"KRX:{code}", "type": tr_type}
            for code in stock_codes
        ]
        
        message = {
            "header": {
                "api-id": tr_type,
                "authorization": f"Bearer {self.token}"
            },
            "body": {
                "trnm": "REMOVE",
                "grp_no": "0001",
                "data": data_list
            }
        }
        
        self.ws.send(json.dumps(message))

# 사용 예시
def on_price_update(data):
    """실시간 체결 데이터 콜백"""
    print(f"시간: {data.get('20')}")
    print(f"현재가: {data.get('10')}")
    print(f"거래량: {data.get('15')}")
    print("-" * 50)

# WebSocket 연결
ws_client = KiwoomWebSocket(token=access_token, is_mock=True)
ws_client.connect()

# 삼성전자, SK하이닉스 실시간 체결 등록
ws_client.subscribe(
    stock_codes=["005930", "000660"],
    tr_type="0B",  # 주식체결
    callback=on_price_update
)

# 프로그램 계속 실행
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("프로그램 종료")
```

---

## 코드 구현 예제

### 🔧 완전한 API 클라이언트 클래스

```python
import requests
import json
from typing import Optional, Dict, List
from datetime import datetime, timedelta

class KiwoomAPIClient:
    """키움증권 REST API 클라이언트"""
    
    def __init__(self, appkey: str, secretkey: str, is_mock: bool = False):
        """
        초기화
        
        Args:
            appkey: App Key
            secretkey: Secret Key
            is_mock: True면 모의투자 환경
        """
        self.appkey = appkey
        self.secretkey = secretkey
        self.is_mock = is_mock
        
        # Base URL 설정
        if is_mock:
            self.base_url = "https://mockapi.kiwoom.com"
        else:
            self.base_url = "https://api.kiwoom.com"
        
        # 토큰 정보
        self.token = None
        self.token_expires = None
        
    def _ensure_token(self):
        """토큰 확인 및 자동 갱신"""
        if not self.token or datetime.now() >= self.token_expires:
            self._get_token()
    
    def _get_token(self):
        """접근 토큰 발급"""
        url = f"{self.base_url}/oauth2/token"
        
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "secretkey": self.secretkey
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('return_code') == 0:
                self.token = data['token']
                # 만료 시간 설정 (24시간 - 1시간 여유)
                self.token_expires = datetime.now() + timedelta(hours=23)
            else:
                raise Exception(f"Token Error: {data.get('return_msg')}")
        else:
            raise Exception(f"HTTP Error: {response.status_code}")
    
    def _make_request(
        self, 
        method: str, 
        url: str, 
        api_id: str, 
        body: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        API 요청 공통 메서드
        
        Args:
            method: HTTP 메서드 (GET, POST)
            url: API 엔드포인트
            api_id: API ID
            body: Request Body
            params: Query Parameters
        
        Returns:
            dict: API 응답
        """
        self._ensure_token()
        
        headers = {
            "api-id": api_id,
            "authorization": f"Bearer {self.token}",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        full_url = f"{self.base_url}{url}"
        
        if method.upper() == "POST":
            response = requests.post(full_url, headers=headers, json=body)
        else:
            response = requests.get(full_url, headers=headers, params=params)
        
        return response.json()
    
    # ========== 계좌 정보 ==========
    
    def get_balance(self, qry_tp: str = "1", exchange: str = "KRX") -> Dict:
        """
        계좌 평가 잔고 조회
        
        Args:
            qry_tp: 조회구분 (1:합산, 2:개별)
            exchange: 거래소 (KRX, NXT)
        
        Returns:
            dict: 계좌 잔고 정보
        """
        body = {
            "qry_tp": qry_tp,
            "dmst_stex_tp": exchange
        }
        
        return self._make_request("POST", "/api/dostk/acnt", "kt00018", body)
    
    def get_open_orders(self, stock_code: str = "", exchange: str = "KRX") -> Dict:
        """
        미체결 주문 조회
        
        Args:
            stock_code: 종목코드 (빈값이면 전체)
            exchange: 거래소
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }
        
        return self._make_request("POST", "/api/dostk/acnt", "ka10075", body)
    
    def get_executed_orders(self, stock_code: str = "", exchange: str = "KRX") -> Dict:
        """체결 주문 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }
        
        return self._make_request("POST", "/api/dostk/acnt", "ka10076", body)
    
    # ========== 주문 ==========
    
    def buy(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "3",
        exchange: str = "KRX"
    ) -> Dict:
        """
        매수 주문
        
        Args:
            stock_code: 종목코드
            quantity: 주문수량
            price: 주문가격 (0이면 시장가)
            order_type: 매매구분 (0:지정가, 3:시장가)
            exchange: 거래소
        
        Returns:
            dict: 주문 결과 (ord_no 포함)
        """
        body = {
            "dmst_stex_tp": exchange,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": order_type,
            "cond_uv": ""
        }
        
        return self._make_request("POST", "/api/dostk/ordr", "kt10000", body)
    
    def sell(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "3",
        exchange: str = "KRX"
    ) -> Dict:
        """매도 주문"""
        body = {
            "dmst_stex_tp": exchange,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price) if price > 0 else "",
            "trde_tp": order_type,
            "cond_uv": ""
        }
        
        return self._make_request("POST", "/api/dostk/ordr", "kt10001", body)
    
    def modify_order(
        self,
        org_order_no: str,
        stock_code: str,
        quantity: int,
        price: int,
        order_type: str = "0",
        exchange: str = "KRX"
    ) -> Dict:
        """주문 정정"""
        body = {
            "dmst_stex_tp": exchange,
            "org_ord_no": org_order_no,
            "stk_cd": stock_code,
            "ord_qty": str(quantity),
            "ord_uv": str(price),
            "trde_tp": order_type
        }
        
        return self._make_request("POST", "/api/dostk/ordr", "kt10002", body)
    
    def cancel_order(
        self,
        org_order_no: str,
        stock_code: str,
        quantity: int,
        exchange: str = "KRX"
    ) -> Dict:
        """주문 취소"""
        body = {
            "dmst_stex_tp": exchange,
            "org_ord_no": org_order_no,
            "stk_cd": stock_code,
            "ord_qty": str(quantity)
        }
        
        return self._make_request("POST", "/api/dostk/ordr", "kt10003", body)
    
    # ========== 시세 정보 ==========
    
    def get_current_price(self, stock_code: str, exchange: str = "KRX") -> Dict:
        """현재가 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }
        
        return self._make_request("POST", "/api/dostk/stkinfo", "ka10001", body)
    
    def get_orderbook(self, stock_code: str, exchange: str = "KRX") -> Dict:
        """호가 조회"""
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange
        }
        
        return self._make_request("POST", "/api/dostk/mrkcond", "ka10004", body)
    
    # ========== 차트 데이터 ==========
    
    def get_daily_chart(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        exchange: str = "KRX"
    ) -> Dict:
        """
        일봉 차트 조회
        
        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            exchange: 거래소
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange,
            "inqr_strt_dt": start_date,
            "inqr_end_dt": end_date
        }
        
        return self._make_request("POST", "/api/dostk/chart", "ka10081", body)
    
    def get_minute_chart(
        self,
        stock_code: str,
        date: str,
        time_type: str = "1",
        exchange: str = "KRX"
    ) -> Dict:
        """
        분봉 차트 조회
        
        Args:
            stock_code: 종목코드
            date: 조회일 (YYYYMMDD)
            time_type: 시간구분 (1:1분, 3:3분, 5:5분, 10:10분, 30:30분, 60:60분)
            exchange: 거래소
        """
        body = {
            "stk_cd": stock_code,
            "dmst_stex_tp": exchange,
            "time_tp": time_type,
            "inqr_strt_dt": date,
            "inqr_end_dt": date
        }
        
        return self._make_request("POST", "/api/dostk/chart", "ka10080", body)
    
    # ========== 종목 정보 ==========
    
    def get_stock_list(self, market_type: str = "ALL") -> Dict:
        """
        종목 리스트 조회
        
        Args:
            market_type: 시장구분 (ALL, KOSPI, KOSDAQ, ETF, ETN)
        """
        body = {
            "mkt_tp": market_type
        }
        
        return self._make_request("POST", "/api/dostk/stkinfo", "ka10099", body)

# ========== 사용 예시 ==========

# 클라이언트 초기화
client = KiwoomAPIClient(
    appkey="YOUR_APP_KEY",
    secretkey="YOUR_SECRET_KEY",
    is_mock=True  # 모의투자 환경
)

# 1. 계좌 잔고 조회
balance = client.get_balance()
print("총평가금액:", balance.get('tot_evlt_amt'))
print("총평가손익:", balance.get('tot_evlt_pl'))

# 2. 삼성전자 현재가 조회
price_info = client.get_current_price("005930")
print("현재가:", price_info.get('now_uv'))

# 3. 삼성전자 10주 시장가 매수
buy_result = client.buy(
    stock_code="005930",
    quantity=10,
    order_type="3"  # 시장가
)
print("주문번호:", buy_result.get('ord_no'))

# 4. 미체결 주문 조회
open_orders = client.get_open_orders()
print("미체결 주문 수:", len(open_orders.get('data', [])))

# 5. 일봉 데이터 조회 (최근 30일)
from datetime import datetime, timedelta
end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

chart_data = client.get_daily_chart("005930", start_date, end_date)
for candle in chart_data.get('data', []):
    print(f"{candle['stck_bsop_date']}: 종가 {candle['stck_clpr']}")
```

---

## 에러 처리

### 🚨 응답 코드

모든 API 응답은 다음 구조를 포함합니다:

```json
{
  "return_code": 0,
  "return_msg": "정상적으로 처리되었습니다"
}
```

| return_code | 설명 |
|-------------|------|
| `0` | 정상 처리 |
| `1` | 오류 발생 |

### ⚠️ 일반적인 오류 상황

1. **토큰 만료**
   - return_msg: "토큰이 만료되었습니다"
   - 해결: 토큰 재발급

2. **API 호출 제한**
   - 시간당 호출 횟수 제한
   - 해결: 요청 간격 조절

3. **잘못된 파라미터**
   - return_msg: "필수 파라미터 누락" 등
   - 해결: 요청 파라미터 확인

4. **IP 미등록**
   - return_msg: "등록되지 않은 IP입니다"
   - 해결: 키움증권 사이트에서 IP 등록

### 🛡️ 에러 처리 예제

```python
def safe_api_call(func):
    """API 호출 에러 처리 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # return_code 확인
            if result.get('return_code') != 0:
                raise Exception(f"API Error: {result.get('return_msg')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    return wrapper

# 사용 예시
@safe_api_call
def get_balance_safe(client):
    return client.get_balance()
```

---

## 📚 추가 리소스

### 공식 사이트

- **API 가이드**: https://openapi.kiwoom.com
- **키움증권 홈페이지**: https://www.kiwoom.com

### 중요 공지사항

1. **보안**
   - App Key/Secret Key는 절대 노출하지 마세요
   - GitHub 등 공개 저장소에 업로드 금지
   - 환경변수 또는 별도 설정 파일로 관리

2. **API 사용 제한**
   - 과도한 API 호출 자제
   - 실시간 데이터는 필요한 종목만 등록
   - 불필요한 데이터는 즉시 해제

3. **모의투자 활용**
   - 실전 투자 전 반드시 모의투자로 충분한 테스트
   - 모의투자는 KRX만 지원 (NXT 미지원)

4. **책임**
   - API를 통한 실제 거래는 사용자 본인의 책임
   - 손실 발생 시 키움증권이나 개발자는 책임지지 않음

---

## 🎯 다음 단계

1. ✅ 키움증권 계좌 개설
2. ✅ REST API 신청 및 App Key 발급
3. ✅ IP 주소 등록
4. ✅ 모의투자 환경에서 테스트
5. ✅ 실전 투자 시작

---

**문서 버전**: 1.0.0  
**최종 업데이트**: 2025년 10월 20일  
**작성자**: Claude (Anthropic)

**면책 조항**: 이 문서는 키움증권 REST API의 공식 문서를 기반으로 작성되었으며, 실제 투자에 따른 손실에 대해서는 어떠한 책임도 지지 않습니다. 투자는 본인의 판단과 책임하에 진행하시기 바랍니다.
