# 📘 Phase 1: Sub Server 실행 가이드

> 24시간 틱데이터 수집 서버 구동 가이드

## 🎯 Phase 1 완료 현황

### ✅ 구현 완료 기능

1. **거래대금 TOP 50 종목 자동 수집**
   - REST API `ka10032` 활용
   - 1회 호출로 효율적 조회
   - 관리종목 자동 제외

2. **실시간 틱데이터 수집 엔진**
   - WebSocket 연결 및 재연결 로직
   - 버퍼링 시스템 (기본 10,000건)
   - 주기적 DB 플러시 (기본 10초)

3. **DB 저장 서비스**
   - 대량 삽입 (bulk insert) 최적화
   - 자동 재연결
   - 트랜잭션 관리

4. **모니터링 대시보드**
   - 실시간 통계 웹 대시보드
   - REST API 엔드포인트
   - 시스템 헬스 체크

5. **로깅 시스템**
   - 컬러 콘솔 출력
   - 파일 로테이션 (크기/날짜 기반)
   - 컴포넌트별 로그 분리

---

## 🚀 빠른 시작

### 1. 사전 준비

#### 필수 소프트웨어 설치

```bash
# MariaDB 설치 (Ubuntu/Debian)
sudo apt update
sudo apt install mariadb-server
sudo systemctl start mariadb

# Redis 설치
sudo apt install redis-server
sudo systemctl start redis
```

#### Python 가상환경 설정

```bash
cd /home/nbg/Desktop/kium2

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 초기화

```bash
# MariaDB 접속
mysql -u root -p

# 스키마 생성
source database/schema.sql

# 확인
USE gslts_trading;
SHOW TABLES;
```

**출력 예시:**
```
+------------------------------+
| Tables_in_gslts_trading      |
+------------------------------+
| daily_candle                 |
| minute_candle                |
| orders                       |
| sector_mapping               |
| stock_master                 |
| system_logs                  |
| tick_data                    |
| trading_volume_rank          |
| us_sector_data               |
+------------------------------+
```

### 3. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**필수 설정:**
```bash
# 키움증권 API 인증
KIWOOM_APP_KEY=your_app_key_here
KIWOOM_SECRET_KEY=your_secret_key_here
KIWOOM_IS_MOCK=true  # 모의투자 환경

# 데이터베이스
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gslts_trading

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Sub Server
SUB_SERVER_PORT=8001

# 수집 설정
COLLECT_STOCK_COUNT=50
TICK_BUFFER_SIZE=10000
FLUSH_INTERVAL=10

# 로깅
LOG_LEVEL=INFO
```

### 4. Sub Server 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# Sub Server 시작
python sub_server/main.py
```

**성공 시 출력:**
```
============================================================
로깅 시스템 초기화 완료
============================================================
로그 디렉토리: /home/nbg/Desktop/kium2/logs
로그 레벨: INFO

============================================================
Sub Server 초기화
============================================================
모의투자 모드: True
✅ 토큰 발급 성공
🌐 모니터링 대시보드 시작: http://localhost:8001/dashboard
✅ 초기화 완료

============================================================
🚀 Sub Server 시작
============================================================
📊 거래대금 TOP 50 종목 수집 중...

============================================================
📈 거래대금 TOP 5
============================================================
 1위 | 삼성전자      (005930) | 거래대금: 500,000,000,000원 | 현재가: 75,000원 | 등락율:  1.35%
 2위 | SK하이닉스    (000660) | 거래대금: 300,000,000,000원 | 현재가: 120,000원 | 등락율:  2.10%
 ...
============================================================

✅ 틱데이터 수집 시작 완료
⏰ 주기적 플러시 시작 (10초마다)

============================================================
✅ Sub Server 가동 중...
Ctrl+C로 종료
============================================================
```

---

## 📊 모니터링 대시보드

### 웹 대시보드 접속

```
http://localhost:8001/dashboard
```

### API 엔드포인트

#### 1. 전체 상태 조회
```bash
curl http://localhost:8001/api/status | jq
```

**응답 예시:**
```json
{
  "collector": {
    "is_running": true,
    "tick_count": 125430,
    "ticks_per_second": 45.2,
    "stock_count": 50
  },
  "database": {
    "today_count": 125430,
    "size": "1.23 GB"
  },
  "system": {
    "cpu_percent": 12.5,
    "memory_percent": 45.3,
    "disk_percent": 65.1
  }
}
```

#### 2. 헬스 체크
```bash
curl http://localhost:8001/api/health
```

#### 3. 시스템 정보
```bash
curl http://localhost:8001/api/system
```

---

## 📈 데이터 확인

### 틱데이터 조회

```sql
-- 최근 100개 틱데이터
SELECT
    stock_code,
    tick_time,
    price,
    volume,
    change_rate
FROM tick_data
ORDER BY tick_time DESC
LIMIT 100;

-- 종목별 오늘 통계
SELECT * FROM v_today_tick_stats;
```

### 거래대금 랭킹 조회

```sql
-- 최신 TOP 50
SELECT * FROM v_top_trading_stocks;

-- 특정 시간대 랭킹
SELECT
    stock_code,
    stock_name,
    trading_value,
    rank_position,
    collected_at
FROM trading_volume_rank
WHERE collected_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
ORDER BY collected_at DESC, rank_position;
```

---

## 🛠️ 운영 가이드

### 로그 확인

```bash
# 전체 로그
tail -f logs/sub_server.log

# 에러 로그만
tail -f logs/error.log

# 컬렉터 로그
tail -f logs/collector.log

# 오늘 로그
tail -f logs/daily_$(date +%Y%m%d).log
```

### 성능 튜닝

#### 버퍼 크기 조정
```bash
# .env 파일
TICK_BUFFER_SIZE=20000  # 기본: 10000
```

#### 플러시 주기 조정
```bash
# .env 파일
FLUSH_INTERVAL=5  # 기본: 10초
```

#### 수집 종목 수 조정
```bash
# .env 파일
COLLECT_STOCK_COUNT=100  # 기본: 50
```

### 데이터베이스 최적화

#### 인덱스 추가 (데이터 증가 시)
```sql
-- 복합 인덱스 추가
ALTER TABLE tick_data
ADD INDEX idx_stock_time_price (stock_code, tick_time, price);

-- 파티션 추가 (월별)
ALTER TABLE tick_data
PARTITION BY RANGE (YEAR(tick_time) * 100 + MONTH(tick_time)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    ...
);
```

#### 오래된 데이터 정리
```sql
-- 30일 이전 틱데이터 삭제
DELETE FROM tick_data
WHERE tick_time < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 오래된 랭킹 데이터 삭제
DELETE FROM trading_volume_rank
WHERE collected_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
```

---

## 🔧 트러블슈팅

### 1. 토큰 발급 실패

**증상:**
```
❌ 토큰 발급 실패: HTTP Error: 401
```

**해결:**
- `.env` 파일의 `KIWOOM_APP_KEY`, `KIWOOM_SECRET_KEY` 확인
- 키움증권 홈페이지에서 키 재발급
- IP 화이트리스트 등록 확인

### 2. WebSocket 연결 실패

**증상:**
```
❌ WebSocket 연결 실패
```

**해결:**
- 네트워크 연결 확인
- 방화벽 설정 확인 (포트 10000)
- 모의투자/실전투자 URL 확인

### 3. DB 연결 실패

**증상:**
```
❌ DB 연결 실패: Access denied
```

**해결:**
```sql
-- MariaDB 사용자 생성
CREATE USER 'kium_user'@'localhost' IDENTIFIED BY 'kium_password';
GRANT ALL PRIVILEGES ON gslts_trading.* TO 'kium_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 메모리 부족

**증상:**
```
Out of memory
```

**해결:**
- 버퍼 크기 감소: `TICK_BUFFER_SIZE=5000`
- 플러시 주기 단축: `FLUSH_INTERVAL=5`
- 수집 종목 수 감소: `COLLECT_STOCK_COUNT=30`

---

## 📊 성능 지표

### 목표 성능
- **수집 속도**: 40-60건/초
- **DB 저장 지연**: < 1초
- **메모리 사용량**: < 500MB
- **CPU 사용률**: < 30%

### 일일 예상 데이터량
```
종목 수: 50개
평균 틱/분: 10개
거래시간: 6.5시간 (09:00-15:30)

일일 틱데이터 = 50 * 10 * 390분 = 195,000건
월간 틱데이터 = 195,000 * 20일 = 3,900,000건 (약 400만건)
```

---

## 🎯 다음 단계 (Phase 2)

Phase 1 완료 후 진행할 내용:

1. **Main Server 구축**
   - FastAPI 백엔드
   - 주문 API (매수/매도/정정/취소)
   - 실시간 호가창 WebSocket

2. **Frontend 개발**
   - React 웹 애플리케이션
   - TradingView 차트 통합
   - 원페이지 트레이딩 UI

3. **미국 섹터 연동**
   - 미국 섹터 ETF 데이터 수집
   - 섹터 기반 종목 추천 엔진
   - 상관관계 분석

---

## 📞 문의 및 지원

- GitHub Issues: [프로젝트 이슈 페이지]
- 키움증권 API 문의: https://openapi.kiwoom.com
- 문서: `/docs` 디렉토리 참조

---

**버전**: 1.0.0 (Phase 1 완료)
**최종 업데이트**: 2025-11-21
