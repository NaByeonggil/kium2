# Sub Server 실행 가이드

24시간 틱데이터 수집 서버 실행 및 모니터링 가이드

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [초기 설정](#초기-설정)
3. [Sub Server 실행](#sub-server-실행)
4. [모니터링 대시보드](#모니터링-대시보드)
5. [로그 확인](#로그-확인)
6. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 필수 소프트웨어

- Python 3.10 이상
- MariaDB 10.6 이상 (또는 MySQL 8.0 이상)
- Redis 6.0 이상 (선택)
- 충분한 디스크 공간 (일일 약 10~50GB 예상)

### Python 패키지

```bash
# 가상환경 활성화
source venv/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt
```

주요 패키지:
- `requests` - REST API 통신
- `websocket-client` - 실시간 데이터 수신
- `pymysql` - 데이터베이스 연결
- `fastapi` - 모니터링 API
- `psutil` - 시스템 모니터링

---

## 초기 설정

### 1. 환경변수 설정

`.env` 파일 확인 및 수정:

```bash
# 키움증권 API 인증 정보
KIWOOM_APP_KEY=your_app_key
KIWOOM_SECRET_KEY=your_secret_key
KIWOOM_IS_MOCK=false

# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=gslts_trading

# 로깅 설정
LOG_DIR=logs
LOG_LEVEL=INFO
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# 데이터 수집 설정
TICK_BUFFER_SIZE=10000
FLUSH_INTERVAL=10

# 모니터링 대시보드 포트
SUB_SERVER_PORT=8001
```

### 2. 데이터베이스 설정

MariaDB 접속:

```bash
mysql -u root -p
```

데이터베이스 및 테이블 생성:

```sql
-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS gslts_trading
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 스키마 파일 실행
USE gslts_trading;
source database/schema.sql;

-- 테이블 확인
SHOW TABLES;
```

### 3. 통합 테스트 실행

시스템이 제대로 설정되었는지 확인:

```bash
# 가상환경 활성화
source venv/bin/activate

# 통합 테스트 실행
python tests/test_integration.py
```

테스트 항목:
- ✅ 환경변수 확인
- ✅ 모듈 임포트
- ✅ 데이터베이스 연결
- ✅ 키움 API 연결
- ✅ 모니터링 서비스
- ✅ 로깅 시스템
- ✅ 대시보드 시작

---

## Sub Server 실행

### 일반 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# Sub Server 실행
python sub_server/main.py
```

### 백그라운드 실행 (nohup)

```bash
# 백그라운드 실행
nohup python sub_server/main.py > logs/nohup.out 2>&1 &

# 프로세스 ID 확인
echo $!

# 실행 중인 프로세스 확인
ps aux | grep main.py
```

### systemd 서비스 등록 (Linux)

`/etc/systemd/system/gslts-sub-server.service` 파일 생성:

```ini
[Unit]
Description=GSLTS Sub Server
After=network.target mariadb.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/kium2
Environment="PATH=/path/to/kium2/venv/bin"
ExecStart=/path/to/kium2/venv/bin/python sub_server/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 시작:

```bash
# 서비스 등록
sudo systemctl daemon-reload
sudo systemctl enable gslts-sub-server

# 서비스 시작
sudo systemctl start gslts-sub-server

# 상태 확인
sudo systemctl status gslts-sub-server

# 로그 확인
sudo journalctl -u gslts-sub-server -f
```

### 종료

```bash
# Ctrl+C로 종료 (포그라운드 실행 시)

# 또는 프로세스 종료
pkill -f "python sub_server/main.py"
```

---

## 모니터링 대시보드

### 대시보드 접속

Sub Server가 실행되면 자동으로 모니터링 대시보드가 시작됩니다.

**대시보드 URL**: http://localhost:8001/dashboard

### API 엔드포인트

#### 1. 전체 상태 조회
```bash
curl http://localhost:8001/api/status
```

응답 예시:
```json
{
  "timestamp": "2024-11-15 15:30:00",
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 32.1
  },
  "collector": {
    "is_running": true,
    "tick_count": 125430,
    "ticks_per_second": 42.3,
    "buffer_size": 3245
  },
  "database": {
    "tick_count_today": 1245678,
    "database_size": "2.45 GB"
  }
}
```

#### 2. 헬스 체크
```bash
curl http://localhost:8001/api/health
```

응답 예시:
```json
{
  "status": "healthy",
  "is_healthy": true,
  "timestamp": "2024-11-15 15:30:00",
  "issues": []
}
```

#### 3. 수집기 통계
```bash
curl http://localhost:8001/api/collector
```

#### 4. 데이터베이스 통계
```bash
curl http://localhost:8001/api/database
```

#### 5. 시스템 리소스
```bash
curl http://localhost:8001/api/system
```

---

## 로그 확인

### 로그 파일 위치

Sub Server는 다음 로그 파일을 생성합니다:

```
logs/
├── sub_server.log          # 통합 로그 (모든 레벨)
├── error.log               # 에러 로그 (ERROR 이상)
├── daily_YYYYMMDD.log      # 일별 로그 (자정마다 로테이션)
├── collector.log           # 수집기 전용 로그
├── api.log                 # API 클라이언트 로그
└── storage.log             # DB 저장 로그
```

### 실시간 로그 확인

```bash
# 통합 로그
tail -f logs/sub_server.log

# 에러 로그만
tail -f logs/error.log

# 수집기 로그
tail -f logs/collector.log

# 색상 있는 로그 (ccze 사용)
tail -f logs/sub_server.log | ccze -A
```

### 로그 검색

```bash
# 오늘 에러 검색
grep ERROR logs/sub_server.log

# 특정 종목 틱데이터 검색
grep "005930" logs/collector.log

# 최근 100줄에서 WARNING 이상 검색
tail -100 logs/sub_server.log | grep -E "WARNING|ERROR|CRITICAL"
```

---

## 문제 해결

### 1. API 연결 실패

**증상**: `❌ OAuth 토큰 발급 실패`

**해결방법**:

1. API 키 확인:
   ```bash
   # .env 파일에서 KIWOOM_APP_KEY, KIWOOM_SECRET_KEY 확인
   cat .env | grep KIWOOM
   ```

2. 키움 시스템 점검 확인:
   - 키움증권 홈페이지에서 시스템 점검 공지 확인
   - 모의투자 서버 점검 시간: 주로 08:30~18:00

3. 네트워크 연결 확인:
   ```bash
   curl -I https://api.kiwoom.com
   ```

### 2. 데이터베이스 연결 실패

**증상**: `❌ DB 연결 실패`

**해결방법**:

1. MariaDB 실행 확인:
   ```bash
   sudo systemctl status mariadb
   ```

2. DB 접속 정보 확인:
   ```bash
   mysql -h localhost -u root -p gslts_trading
   ```

3. 테이블 존재 확인:
   ```sql
   USE gslts_trading;
   SHOW TABLES;
   ```

### 3. 메모리 부족

**증상**: 시스템 메모리 사용률 90% 이상

**해결방법**:

1. 버퍼 크기 줄이기:
   ```bash
   # .env 파일에서
   TICK_BUFFER_SIZE=5000  # 기본값 10000에서 감소
   ```

2. 플러시 주기 단축:
   ```bash
   FLUSH_INTERVAL=5  # 기본값 10초에서 감소
   ```

3. 불필요한 프로세스 종료

### 4. 디스크 공간 부족

**증상**: 디스크 사용률 90% 이상

**해결방법**:

1. 로그 파일 정리:
   ```bash
   # 7일 이전 로그 삭제
   find logs/ -name "*.log.*" -mtime +7 -delete
   ```

2. 오래된 틱데이터 삭제:
   ```sql
   -- 30일 이전 데이터 삭제
   DELETE FROM tick_data
   WHERE tick_time < DATE_SUB(NOW(), INTERVAL 30 DAY);
   ```

3. 파티션 정리 (schema.sql에서 설정한 파티션)

### 5. WebSocket 연결 끊김

**증상**: `WebSocket disconnected`

**해결방법**:

WebSocket 클라이언트는 자동 재연결 기능이 내장되어 있습니다.

- 최대 10회 재연결 시도
- Exponential backoff (2^n초, 최대 60초)
- 재연결 시 구독 목록 자동 복원

수동 재시작이 필요한 경우:
```bash
# Sub Server 재시작
sudo systemctl restart gslts-sub-server
```

### 6. 대시보드 접속 불가

**증상**: `http://localhost:8001` 접속 안 됨

**해결방법**:

1. 포트 확인:
   ```bash
   netstat -tuln | grep 8001
   ```

2. 방화벽 확인:
   ```bash
   sudo ufw status
   sudo ufw allow 8001/tcp
   ```

3. 로그 확인:
   ```bash
   grep "모니터링" logs/sub_server.log
   ```

---

## 성능 최적화 팁

### 1. 데이터베이스 최적화

```sql
-- 인덱스 통계 업데이트
ANALYZE TABLE tick_data;

-- 테이블 최적화 (주기적으로 실행)
OPTIMIZE TABLE tick_data;
```

### 2. 버퍼 크기 조정

시스템 메모리에 따라 버퍼 크기 조정:

- 8GB RAM: `TICK_BUFFER_SIZE=5000`
- 16GB RAM: `TICK_BUFFER_SIZE=10000` (기본값)
- 32GB RAM: `TICK_BUFFER_SIZE=20000`

### 3. 로그 레벨 조정

프로덕션 환경:
```bash
LOG_LEVEL=INFO  # 또는 WARNING
```

개발/디버깅:
```bash
LOG_LEVEL=DEBUG
```

---

## 다음 단계

Sub Server가 안정적으로 실행되면:

1. **Main Server 개발** (Phase 2)
   - FastAPI 백엔드 구현
   - 거래 API 개발
   - Sub Server 연동

2. **Sector Analysis** (Phase 3)
   - 미국 섹터 분석
   - 종목 추천 엔진
   - 상관관계 분석

3. **프론트엔드** (Phase 4)
   - React 대시보드
   - 실시간 차트
   - 거래 인터페이스

---

## 지원

문제가 발생하면:

1. 로그 파일 확인 (`logs/error.log`)
2. 통합 테스트 실행 (`python tests/test_integration.py`)
3. 헬스 체크 확인 (`curl http://localhost:8001/api/health`)

---

**작성일**: 2024-11-15
**버전**: 1.0.0
**프로젝트**: GSLTS (Global Sector Linked Trading System)
