# 📡 키움증권 API 매핑 가이드

## 📋 목차

1. [개요](#개요)
2. [API 카테고리](#api-카테고리)
3. [주요 API 목록](#주요-api-목록)
4. [API 사용 예제](#api-사용-예제)
5. [데이터 구조](#데이터-구조)
6. [참고 자료](#참고-자료)

---

## 개요

이 문서는 영웅문4(HTS) 화면번호와 키움증권 REST API, OPEN API+ TR의 매핑 정보를 제공합니다.

### 매핑 파일 위치

```
config/api_mappings/kiwoom_api_mapping.json
```

### 데이터 구조

```json
{
  "screen_no": "화면번호",
  "screen_name": "화면명",
  "rest_api": "REST API ID",
  "rest_api_name": "REST API 이름",
  "open_api": "OPEN API+ TR ID",
  "open_api_name": "OPEN API+ TR 이름",
  "category": "카테고리"
}
```

---

## API 카테고리

| 카테고리 | 설명 | API 개수 |
|---------|------|---------|
| **account** | 계좌 관련 (예수금, 잔고, 평가) | 15 |
| **quote** | 시세 조회 (현재가, 호가, 차트) | 8 |
| **order** | 주문 (매수, 매도, 정정, 취소) | 3 |
| **trade_history** | 거래 내역 (체결, 미체결) | 7 |
| **stock_info** | 종목 정보 (외국인, 기관, 거래원) | 12 |
| **sector** | 업종/테마 | 5 |
| **elw** | ELW | 12 |
| **etf** | ETF | 4 |
| **program_trading** | 프로그램매매 | 8 |
| **investor** | 투자자동향 | 18 |
| **chart** | 차트 | 6 |
| **ranking** | 순위 | 19 |
| **gold** | 금현물 | 4 |

**총 API 개수**: 약 120개

---

## 주요 API 목록

### 1. 계좌 관련 (account)

#### 예수금 조회
- **화면번호**: 0361, 0362
- **REST API**: `kt00001` - 예수금상세현황요청
- **OPEN API+**: `OPW00001` - 예수금상세현황요청
- **설명**: 계좌의 예수금 정보 조회

#### 계좌 평가 현황
- **화면번호**: 0346, 0366, 0391
- **REST API**: `kt00004` - 계좌평가현황요청
- **OPEN API+**: `OPW00004` - 계좌평가현황요청
- **설명**: 계좌 잔고 및 평가 손익 조회

#### 계좌 수익률
- **화면번호**: 0345, 0309
- **REST API**: `kt00003`, `ka10085` - 추정자산조회요청, 계좌수익률요청
- **OPEN API+**: `OPW00003`, `OPT10085`
- **설명**: 계좌 수익률 및 추정 자산 조회

### 2. 시세 조회 (quote)

#### 체결 정보
- **화면번호**: 0120
- **REST API**: `ka10003` - 체결정보요청
- **OPEN API+**: `OPT10003` - 체결정보요청
- **설명**: 종목의 체결 정보 조회

#### 일별 주가
- **화면번호**: 0124
- **REST API**: `ka10086` - 일별주가요청
- **OPEN API+**: `OPT10086` - 일별주가요청
- **설명**: 종목의 일별 주가 데이터

#### 당일/전일 체결
- **화면번호**: 0122
- **REST API**: `ka10055`, `ka10084`
- **OPEN API+**: `OPT10055`, `OPT10084`
- **설명**: 당일/전일 체결량 조회

### 3. 주문 (order)

#### 주문 가능 수량
- **화면번호**: 0399
- **REST API**: `kt00011`, `kt00012`
- **OPEN API+**: `OPW00011`, `OPW00012`
- **설명**: 종목별 주문 가능 수량 조회

#### 주문 인출 가능금
- **화면번호**: 0347
- **REST API**: `kt00010` - 주문인출가능금액요청
- **OPEN API+**: `OPW00010`
- **설명**: 주문 및 인출 가능 금액 조회

### 4. 거래 내역 (trade_history)

#### 미체결 조회
- **화면번호**: 0341, 0309
- **REST API**: `ka10075` - 미체결요청
- **OPEN API+**: `OPT10075` - 실시간미체결요청
- **설명**: 미체결 주문 내역 조회

#### 체결 확인
- **화면번호**: 0350
- **REST API**: `ka10076` - 체결요청
- **OPEN API+**: `OPT10076` - 실시간체결요청
- **설명**: 체결된 주문 내역 조회

#### 주문 체결 내역
- **화면번호**: 0351, 0352
- **REST API**: `kt00007`, `kt00008`
- **OPEN API+**: `OPW00007`, `OPW00008`
- **설명**: 금일/전일 주문 체결 내역

### 5. 종목 정보 (stock_info)

#### 거래원 정보
- **화면번호**: 0126, 0129, 0254
- **REST API**: `ka10040` - 당일주요거래원요청
- **OPEN API+**: `OPT10040`, `OPT10070`
- **설명**: 거래원 매매 동향

#### 신용매매 동향
- **화면번호**: 0141
- **REST API**: `ka10013` - 신용매매동향요청
- **OPEN API+**: `OPT10013`
- **설명**: 종목별 신용매매 동향

#### 공매도 추이
- **화면번호**: 0142
- **REST API**: `ka10014` - 공매도추이요청
- **OPEN API+**: `OPT10014`
- **설명**: 종목별 공매도 추이

### 6. 순위 (ranking)

#### 거래대금 상위
- **화면번호**: 0186
- **REST API**: `ka10032` - 거래대금상위요청
- **OPEN API+**: `OPT10032`
- **설명**: 거래대금 상위 종목 조회

#### 거래량 급증
- **화면번호**: 0168
- **REST API**: `ka10023` - 거래량급증요청
- **OPEN API+**: `OPT10023`
- **설명**: 거래량 급증 종목

#### 등락률 상위
- **화면번호**: 0181, 0182
- **REST API**: `ka10027`, `ka10028`
- **OPEN API+**: `OPT10027`, `OPT10028`
- **설명**: 전일/시가 대비 등락률 상위

### 7. 차트 (chart)

#### 주식 일/주/월봉
- **화면번호**: 6600, 0613
- **REST API**: `ka10081`, `ka10082`, `ka10083`
- **OPEN API+**: `OPT10081`, `OPT10082`, `OPT10083`
- **설명**: 주식 일봉, 주봉, 월봉 차트

#### 주식 틱/분봉
- **화면번호**: 0612, 0615
- **REST API**: `ka10079`, `ka10080`
- **OPEN API+**: `OPT10079`, `OPT10080`
- **설명**: 주식 틱차트, 분봉차트

### 8. 투자자 동향 (investor)

#### 외국인 매매 동향
- **화면번호**: 0240
- **REST API**: `ka10008` - 주식외국인종목별매매동향
- **OPEN API+**: `OPT10008`
- **설명**: 종목별 외국인 매매 동향

#### 기관 매매 추이
- **화면번호**: 0258
- **REST API**: `ka10045` - 종목별기관매매추이요청
- **OPEN API+**: `OPT10045`
- **설명**: 종목별 기관 매매 추이

#### 증권사별 매매
- **화면번호**: 0251, 0252
- **REST API**: `ka10038`, `ka10039`
- **OPEN API+**: `OPT10038`, `OPT10039`
- **설명**: 증권사별 매매 동향

---

## API 사용 예제

### Python 예제

```python
from sub_server.api.kiwoom_client import KiwoomAPIClient

# 클라이언트 초기화
client = KiwoomAPIClient(
    appkey="your_app_key",
    secretkey="your_secret_key",
    is_mock=True
)

# 1. 거래대금 상위 조회 (ka10032)
response = client.request(
    api_id="ka10032",
    params={
        "시장구분": "0",  # 0: 코스피, 10: 코스닥
        "정렬구분": "1",  # 1: 거래대금
        "대상구분": "0"   # 0: 전체
    }
)

print(f"거래대금 TOP 10:")
for stock in response['output'][:10]:
    print(f"{stock['종목명']}: {stock['거래대금']:,}원")

# 2. 주식 현재가 조회 (ka10001)
response = client.request(
    api_id="ka10001",
    params={
        "종목코드": "005930"  # 삼성전자
    }
)

print(f"종목: {response['종목명']}")
print(f"현재가: {response['현재가']:,}원")
print(f"등락율: {response['등락율']}%")

# 3. 계좌 잔고 조회 (kt00004)
response = client.request(
    api_id="kt00004",
    params={
        "계좌번호": "1234567890",
        "비밀번호": "0000"
    }
)

print(f"총평가금액: {response['총평가금액']:,}원")
print(f"총평가손익: {response['총평가손익']:,}원")
```

### cURL 예제

```bash
# 1. 토큰 발급
curl -X POST "https://openapi.kiwoom.com/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "appkey=YOUR_APP_KEY" \
  -d "appsecretkey=YOUR_SECRET_KEY"

# 2. 거래대금 상위 조회
curl -X GET "https://openapi.kiwoom.com/api/dostk/stkinfo?FID_COND_MRKT_DIV_CODE=0" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "appkey: YOUR_APP_KEY" \
  -H "appsecretkey: YOUR_SECRET_KEY"

# 3. 계좌 잔고 조회
curl -X GET "https://openapi.kiwoom.com/api/dostk/acnt?CANO=12345678&ACNT_PRDT_CD=01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "appkey: YOUR_APP_KEY" \
  -H "appsecretkey: YOUR_SECRET_KEY"
```

---

## 데이터 구조

### JSON 매핑 파일 로드

```python
import json

# API 매핑 파일 로드
with open('config/api_mappings/kiwoom_api_mapping.json', 'r', encoding='utf-8') as f:
    api_mapping = json.load(f)

# 카테고리별 API 필터링
account_apis = [
    api for api in api_mapping['apis']
    if api['category'] == 'account'
]

# 특정 화면번호로 API 찾기
def find_api_by_screen_no(screen_no: str):
    for api in api_mapping['apis']:
        if api['screen_no'] == screen_no:
            return api
    return None

# 예시
api_info = find_api_by_screen_no('0186')
print(api_info)
# 출력:
# {
#   "screen_no": "0186",
#   "screen_name": "거래대금상위",
#   "rest_api": "ka10032",
#   "rest_api_name": "거래대금상위요청",
#   "open_api": "OPT10032",
#   "open_api_name": "거래대금상위요청",
#   "category": "ranking"
# }
```

### API 헬퍼 클래스

```python
class KiwoomAPIMapper:
    """키움 API 매핑 헬퍼"""

    def __init__(self, mapping_file: str):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.apis = self.data['apis']
        self.categories = self.data['categories']

    def get_by_screen_no(self, screen_no: str):
        """화면번호로 API 찾기"""
        for api in self.apis:
            if api['screen_no'] == screen_no:
                return api
        return None

    def get_by_rest_api(self, rest_api_id: str):
        """REST API ID로 API 찾기"""
        results = []
        for api in self.apis:
            if isinstance(api['rest_api'], list):
                if rest_api_id in api['rest_api']:
                    results.append(api)
            elif api['rest_api'] == rest_api_id:
                results.append(api)
        return results

    def get_by_category(self, category: str):
        """카테고리별 API 목록"""
        return [api for api in self.apis if api['category'] == category]

    def search(self, keyword: str):
        """키워드로 검색"""
        results = []
        keyword = keyword.lower()
        for api in self.apis:
            if (keyword in api['screen_name'].lower() or
                keyword in api.get('rest_api_name', '').lower() or
                keyword in api.get('open_api_name', '').lower()):
                results.append(api)
        return results

# 사용 예제
mapper = KiwoomAPIMapper('config/api_mappings/kiwoom_api_mapping.json')

# 거래대금 관련 API 검색
apis = mapper.search('거래대금')
for api in apis:
    print(f"{api['screen_no']}: {api['screen_name']} - {api['rest_api']}")

# 계좌 카테고리 API 목록
account_apis = mapper.get_by_category('account')
print(f"계좌 관련 API: {len(account_apis)}개")
```

---

## 참고 자료

### 공식 문서

- [키움증권 REST API 공식 홈페이지](https://openapi.kiwoom.com/)
- [키움 OPEN API+ 개발 가이드](https://www.kiwoom.com/h/customer/download/VOpenApiInfoView)
- [영웅문4 HTS 사용 가이드](https://www.kiwoom.com/)

### 관련 파일

- API 매핑 JSON: `config/api_mappings/kiwoom_api_mapping.json`
- API 클라이언트: `sub_server/api/kiwoom_client.py`
- WebSocket 클라이언트: `sub_server/api/websocket_client.py`

### 카테고리 설명

| 카테고리 ID | 한글명 |
|------------|--------|
| account | 계좌 관련 |
| quote | 시세 조회 |
| order | 주문 |
| trade_history | 거래 내역 |
| stock_info | 종목 정보 |
| sector | 업종/테마 |
| elw | ELW |
| etf | ETF |
| program_trading | 프로그램매매 |
| investor | 투자자동향 |
| chart | 차트 |
| ranking | 순위 |
| gold | 금현물 |

---

**버전**: 1.0.0
**최종 업데이트**: 2025-11-20
**총 API 개수**: 약 120개
