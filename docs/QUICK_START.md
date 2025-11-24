# 🚀 빠른 시작 가이드

## 📋 목차

1. [Docker로 시작하기 (권장)](#docker로-시작하기-권장)
2. [로컬 환경에서 시작하기](#로컬-환경에서-시작하기)
3. [서비스 확인](#서비스-확인)
4. [다음 단계](#다음-단계)

---

## Docker로 시작하기 (권장)

### 1. 사전 준비

```bash
# Docker 설치 확인
docker --version
docker compose version

# Git 클론 (또는 프로젝트 디렉토리로 이동)
cd /home/nbg/Desktop/kium2
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 키움 API 키 입력 (필수!)
nano .env
```

**필수 설정**:
```env
KIWOOM_APP_KEY=your_app_key_here
KIWOOM_SECRET_KEY=your_secret_key_here
KIWOOM_IS_MOCK=true
```

### 3. Docker Compose 실행

```bash
# 전체 스택 시작 (Sub Server + MariaDB + Redis + Monitoring)
docker compose up -d

# 로그 확인
docker compose logs -f sub-server
```

**실행 결과**:
```
✅ MariaDB 연결 성공: mariadb:3306
✅ Redis 연결 성공: redis:6379
🚀 Sub Server 시작
📊 거래대금 TOP 50 종목 수집 중...
✅ 수집 대상: 50개 종목
```

### 4. 서비스 접속

| 서비스 | URL | 계정 |
|--------|-----|------|
| Sub Server API | http://localhost:8001/api/status | - |
| Sub Server Dashboard | http://localhost:8001/dashboard | - |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| phpMyAdmin | http://localhost:8080 | kium_user / kium_password |
| Redis Commander | http://localhost:8081 | - |

### 5. 관리 도구 사용 (선택)

```bash
# Redis Commander, phpMyAdmin 시작
docker compose --profile tools up -d

# 중지
docker compose --profile tools down
```

---

## 로컬 환경에서 시작하기

### 1. 사전 준비

```bash
# Python 3.9+ 설치 확인
python3 --version

# MariaDB 설치
sudo apt install mariadb-server

# Redis 설치
sudo apt install redis-server
```

### 2. Python 가상환경 설정

```bash
# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 3. 데이터베이스 초기화

```bash
# MariaDB 접속
mysql -u root -p

# 스키마 생성
source database/schema.sql

# 종료
exit
```

### 4. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 설정 편집
nano .env
```

**로컬 환경 설정**:
```env
KIWOOM_APP_KEY=your_app_key_here
KIWOOM_SECRET_KEY=your_secret_key_here
KIWOOM_IS_MOCK=true

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_db_password

REDIS_HOST=localhost
REDIS_PORT=6379
```

### 5. Sub Server 실행

```bash
# Sub Server 시작
python -m sub_server.main
```

---

## 서비스 확인

### 1. API 상태 확인

```bash
# Sub Server API
curl http://localhost:8001/api/status

# 출력 예시:
{
  "status": "running",
  "tick_count": 15234,
  "ticks_per_second": 12.5,
  "buffer_size": 150,
  "stock_count": 50,
  "is_running": true
}
```

### 2. 데이터베이스 확인

```bash
# Docker
docker compose exec mariadb mysql -u kium_user -p gslts_trading

# 로컬
mysql -u root -p gslts_trading

# 쿼리
SELECT COUNT(*) FROM tick_data;
SELECT * FROM trading_volume_rank ORDER BY rank_position LIMIT 10;
```

### 3. Redis 확인

```bash
# Docker
docker compose exec redis redis-cli

# 로컬
redis-cli

# 명령어
PING
INFO
KEYS *
GET tick:005930:latest
```

### 4. 로그 확인

```bash
# Docker
docker compose logs -f sub-server

# 로컬
tail -f logs/sub_server.log
```

---

## 다음 단계

### 1. 모니터링 설정

Grafana에서 대시보드 확인:
1. http://localhost:3000 접속
2. 로그인: `admin` / `admin`
3. Dashboards → Sub Server 대시보드 선택

### 2. API 테스트

```bash
# API 테스트 실행
python tests/test_kiwoom_api.py

# 통합 테스트
python tests/test_integration.py
```

### 3. 데이터 수집 확인

```bash
# 실시간 통계
docker compose exec sub-server python -c "
from sub_server.services.storage_service import TickStorageService
storage = TickStorageService()
print(f'오늘 수집: {storage.get_tick_count_today():,}건')
print(f'DB 크기: {storage.get_database_size()}')
"
```

### 4. 문서 읽기

- [Docker 사용 가이드](./DOCKER_GUIDE.md) - 전체 도커 설명
- [API 매핑 가이드](./API_MAPPING.md) - 키움 API 매핑
- [README.md](../README.md) - 프로젝트 개요

---

## 문제 해결

### Docker 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker compose logs sub-server

# 컨테이너 재시작
docker compose restart sub-server

# 전체 재시작
docker compose down && docker compose up -d
```

### 데이터베이스 연결 오류

```bash
# MariaDB 상태 확인
docker compose ps mariadb

# 스키마 재생성
docker compose exec mariadb mysql -u root -p < database/schema.sql
```

### Redis 연결 오류

```bash
# Redis 상태 확인
docker compose exec redis redis-cli ping

# Redis 재시작
docker compose restart redis
```

### 키움 API 인증 오류

1. `.env` 파일에서 APP_KEY, SECRET_KEY 확인
2. 키움증권 홈페이지에서 API 키 재발급
3. IP 주소 등록 확인

---

## 유용한 명령어

```bash
# 컨테이너 목록
docker compose ps

# 로그 실시간 보기
docker compose logs -f

# 특정 서비스 재시작
docker compose restart sub-server

# 전체 중지
docker compose stop

# 전체 삭제 (데이터 보존)
docker compose down

# 전체 삭제 (데이터 포함)
docker compose down -v

# 서비스 스케일링
docker compose up -d --scale sub-server=2
```

---

**버전**: 1.0.0
**최종 업데이트**: 2025-11-20

**다음 읽을 문서**:
- [Docker 가이드](./DOCKER_GUIDE.md) - 상세 Docker 사용법
- [API 매핑](./API_MAPPING.md) - 키움 API 활용법
