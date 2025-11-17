# 🚀 GSLTS - Global Sector Linked Trading System

> 미국 섹터의 전일 흐름을 분석하여 한국 증시 개장 전 매매 전략을 수립하는 스마트 트레이딩 플랫폼

## 📋 프로젝트 개요

키움증권 REST API를 활용한 증권 거래 시스템으로, 미국-한국 섹터 연동 분석을 통한 종목 추천 및 실시간 매매를 지원합니다.

### 핵심 기능

- ✅ **실시간 틱데이터 수집**: 거래대금 TOP 50 종목 실시간 모니터링
- ✅ **미국 섹터 분석**: 전일 미국 시장 흐름 → 한국 종목 추천
- ✅ **통합 트레이딩 대시보드**: 차트 + 호가창 + 주문 원페이지
- ✅ **백테스팅 엔진**: 틱데이터 기반 전략 검증

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐
│   사용자        │
└────────┬────────┘
         │
┌────────▼────────┐
│  Main Server    │  ← 거래 API, 차트, 주문
│  (FastAPI)      │
└────────┬────────┘
         │
┌────────▼────────┐
│  Sub Server     │  ← 24시간 틱데이터 수집
│  (Data Hub)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  키움증권        │
│  REST API       │
└─────────────────┘
```

## 🚀 빠른 시작

### 1. 사전 준비

#### 필수 요구사항
- Python 3.9+
- MariaDB/MySQL 5.7+
- Redis 7.0+
- 키움증권 계좌

#### 키움 REST API 신청
1. 키움증권 홈페이지 로그인
2. `트레이딩 채널` → `키움 REST API` 메뉴
3. App Key/Secret Key 발급
4. IP 주소 등록 (최대 10개)

### 2. 프로젝트 설정

```bash
# 1. 저장소 클론 (또는 디렉토리 생성)
cd /home/nbg/Desktop/kium2

# 2. Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
nano .env  # App Key, Secret Key 입력
```

### 3. 데이터베이스 초기화

```bash
# MariaDB 접속
mysql -u root -p

# 스키마 생성
source database/schema.sql
```

### 4. API 연결 테스트

```bash
# 키움 REST API 연결 확인
python tests/test_kiwoom_api.py
```

**성공 시 출력**:
```
✅ 토큰 발급 성공!
✅ 현재가 조회 성공!
   종목명: 삼성전자
   현재가: 75000원
   전일대비: +1000원 (+1.35%)
```

## 📁 프로젝트 구조

```
kium2/
├── sub-server/          # 데이터 수집 서버
│   ├── api/             # 키움 API 클라이언트
│   │   ├── kiwoom_client.py       # REST API
│   │   └── websocket_client.py    # WebSocket
│   ├── collectors/      # 틱데이터 수집기
│   ├── models/          # 데이터 모델
│   └── services/        # 비즈니스 로직
│
├── backend/             # Main Server (Phase 2)
│   ├── kiwoom/          # 키움 API 통합
│   ├── routes/          # API 엔드포인트
│   ├── models/          # DB 모델
│   └── services/        # 서비스 로직
│
├── frontend/            # 웹 UI (Phase 2)
│
├── database/            # DB 스키마
│   └── schema.sql
│
├── tests/               # 테스트
│   └── test_kiwoom_api.py
│
├── .env.example         # 환경변수 템플릿
├── requirements.txt     # Python 패키지
└── README.md
```

## 🛠️ 개발 로드맵

### ✅ Phase 0: 환경 구축 (완료)
- [x] 프로젝트 초기화
- [x] 키움 API 클라이언트 작성
- [x] WebSocket 클라이언트 작성
- [x] DB 스키마 설계
- [x] API 연결 테스트

### 🔄 Phase 1: Sub Server (현재 진행 중)
- [ ] 틱데이터 수집 엔진
- [ ] DB 저장 서비스
- [ ] 거래대금 랭킹 수집
- [ ] 모니터링 대시보드

### 📅 Phase 2: Main Server (예정)
- [ ] FastAPI 백엔드
- [ ] 주문 API (매수/매도/정정/취소)
- [ ] 실시간 호가창
- [ ] TradingView 차트 통합

### 📅 Phase 3: 섹터 연동 (예정)
- [ ] 미국 섹터 데이터 수집
- [ ] 섹터 기반 종목 추천 엔진
- [ ] 거래대금 TOP 50 자동 갱신

### 📅 Phase 4: 프리미엄 (예정)
- [ ] 백테스팅 엔진
- [ ] 모바일 앱 (React Native)
- [ ] API 서비스 (유료)

## 🧪 테스트

```bash
# 전체 테스트
pytest

# API 테스트만
python tests/test_kiwoom_api.py

# 코드 포맷팅
black sub-server/ backend/

# 타입 체크
mypy sub-server/
```

## 📖 API 문서

### 키움 REST API 주요 엔드포인트

| API ID | 설명 | URL |
|--------|------|-----|
| `au10001` | OAuth 토큰 발급 | `/oauth2/token` |
| `ka10001` | 주식 현재가 조회 | `/api/dostk/stkinfo` |
| `kt10000` | 주식 매수 주문 | `/api/dostk/ordr` |
| `kt10001` | 주식 매도 주문 | `/api/dostk/ordr` |
| `kt00018` | 계좌 잔고 조회 | `/api/dostk/acnt` |

자세한 API 문서: `키움증권_REST_API_완전가이드.md` 참조

## 🔒 보안

- ⚠️ `.env` 파일은 절대 Git에 커밋하지 마세요
- ⚠️ App Key/Secret Key는 안전하게 보관하세요
- ⚠️ 모의투자 환경에서 충분히 테스트 후 실전 사용하세요

## 📊 성능 목표

| 지표 | 목표 |
|------|------|
| 주문 체결 지연 | < 1초 |
| 틱데이터 수집 정확도 | > 99% |
| 시스템 가동률 | > 99.5% |
| 하루 틱데이터 수집량 | 500만~1,000만 건 |

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

This project is for educational purposes only.

## 🙏 면책 조항

이 시스템은 학습 목적으로 제작되었습니다. 실제 투자에 따른 손실에 대해 개발자는 어떠한 책임도 지지 않습니다. 투자는 본인의 판단과 책임하에 진행하시기 바랍니다.

## 📞 문의

- GitHub Issues: [프로젝트 이슈 페이지]
- 키움증권 API 문의: https://openapi.kiwoom.com

---

**버전**: 0.1.0 (Phase 0 완료)
**최종 업데이트**: 2025-11-15
# kium2
