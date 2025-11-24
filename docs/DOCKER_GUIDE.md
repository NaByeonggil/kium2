# 🐳 Docker 사용 가이드

## 📋 목차

1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [빠른 시작](#빠른-시작)
4. [서비스 구성](#서비스-구성)
5. [Docker Compose 명령어](#docker-compose-명령어)
6. [모니터링](#모니터링)
7. [문제 해결](#문제-해결)
8. [프로덕션 배포](#프로덕션-배포)

---

## 개요

GSLTS Trading System은 Docker Compose를 사용하여 Full Stack 마이크로서비스 아키텍처로 구성되어 있습니다.

### 서비스 구성

- **Sub Server**: 24시간 틱데이터 수집 서버 (Python FastAPI)
- **MariaDB**: 데이터베이스
- **Redis**: 캐싱 & 실시간 데이터
- **Prometheus**: 메트릭 수집
- **Grafana**: 모니터링 대시보드
- **Redis Commander**: Redis 관리 도구 (선택)
- **phpMyAdmin**: MariaDB 관리 도구 (선택)

---

## 사전 준비

### 1. Docker 설치

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose-plugin

# macOS (Homebrew)
brew install docker docker-compose

# Windows
# Docker Desktop 다운로드: https://www.docker.com/products/docker-desktop
```

### 2. Docker 권한 설정 (Linux)

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 키움증권 API 키 입력
nano .env
```

**필수 설정**:
```env
KIWOOM_APP_KEY=your_app_key_here
KIWOOM_SECRET_KEY=your_secret_key_here
```

---

## 빠른 시작

### 전체 스택 실행

```bash
# 1. 프로젝트 루트로 이동
cd /home/nbg/Desktop/kium2

# 2. 컨테이너 빌드 및 실행
docker compose up -d

# 3. 로그 확인
docker compose logs -f sub-server
```

### 서비스 접속

| 서비스 | URL | 설명 |
|--------|-----|------|
| Sub Server API | http://localhost:8001/api/status | 상태 확인 |
| Sub Server Dashboard | http://localhost:8001/dashboard | 모니터링 대시보드 |
| Grafana | http://localhost:3000 | 메트릭 대시보드 |
| Prometheus | http://localhost:9090 | 메트릭 수집 |
| Redis Commander | http://localhost:8081 | Redis 관리 |
| phpMyAdmin | http://localhost:8080 | DB 관리 |

**기본 계정**:
- Grafana: `admin` / `admin`
- phpMyAdmin: `kium_user` / `kium_password`

---

## 서비스 구성

### Sub Server (sub-server)

**기능**:
- 24시간 틱데이터 수집
- 거래대금 TOP 50 종목 모니터링
- WebSocket 실시간 연결
- Redis 캐싱

**포트**: 8001

**헬스체크**:
```bash
curl http://localhost:8001/api/status
```

**로그**:
```bash
docker compose logs -f sub-server
```

### MariaDB (mariadb)

**기능**:
- 틱데이터 저장
- 거래 내역 저장
- 종목 마스터 관리

**포트**: 3306

**접속**:
```bash
# Docker 컨테이너 내부
docker compose exec mariadb mysql -u kium_user -p

# 로컬 MySQL 클라이언트
mysql -h localhost -P 3306 -u kium_user -p
```

**백업**:
```bash
# 데이터베이스 백업
docker compose exec mariadb mysqldump -u root -p gslts_trading > backup.sql

# 복원
docker compose exec -T mariadb mysql -u root -p gslts_trading < backup.sql
```

### Redis (redis)

**기능**:
- 실시간 틱데이터 캐싱
- 거래대금 랭킹 캐싱
- 세션 관리

**포트**: 6379

**CLI 접속**:
```bash
docker compose exec redis redis-cli

# 명령어
PING
INFO
KEYS *
GET tick:005930:latest
```

### Prometheus (prometheus)

**기능**:
- Sub Server 메트릭 수집
- 시스템 메트릭 수집
- 15일간 데이터 보관

**포트**: 9090

### Grafana (grafana)

**기능**:
- 실시간 모니터링 대시보드
- 알림 설정
- 메트릭 시각화

**포트**: 3000

**대시보드**:
- Sub Server 실시간 모니터링
- 틱데이터 수집 현황
- 시스템 리소스 모니터링

---

## Docker Compose 명령어

### 기본 명령어

```bash
# 전체 서비스 시작
docker compose up -d

# 특정 서비스만 시작
docker compose up -d sub-server mariadb redis

# 서비스 중지
docker compose stop

# 서비스 재시작
docker compose restart sub-server

# 서비스 종료 (컨테이너 삭제)
docker compose down

# 볼륨까지 삭제 (⚠️ 데이터 삭제)
docker compose down -v
```

### 로그 확인

```bash
# 전체 로그
docker compose logs

# 특정 서비스 로그
docker compose logs sub-server

# 실시간 로그 (tail -f)
docker compose logs -f sub-server

# 최근 100줄
docker compose logs --tail=100 sub-server
```

### 컨테이너 관리

```bash
# 실행 중인 컨테이너 목록
docker compose ps

# 컨테이너 상세 정보
docker compose ps -a

# 컨테이너 내부 접속
docker compose exec sub-server bash

# 컨테이너 재빌드
docker compose build sub-server

# 강제 재빌드 후 시작
docker compose up -d --build
```

### 리소스 모니터링

```bash
# 컨테이너 리소스 사용량
docker stats

# 특정 컨테이너
docker stats kium2-sub-server

# 디스크 사용량
docker system df

# 볼륨 목록
docker volume ls

# 네트워크 목록
docker network ls
```

---

## 모니터링

### Grafana 대시보드 설정

1. Grafana 접속: http://localhost:3000
2. 로그인: `admin` / `admin`
3. 대시보드 메뉴 → Browse
4. "Sub Server - 실시간 모니터링" 선택

### 주요 메트릭

- **tick_count_total**: 총 수집된 틱데이터 수
- **ticks_per_second**: 초당 틱데이터 수집 속도
- **active_stock_count**: 활성 종목 수
- **buffer_size**: 버퍼 크기
- **process_resident_memory_bytes**: 메모리 사용량

### 알림 설정

Grafana에서 알림 규칙 추가:

1. Dashboard → Edit Panel
2. Alert 탭 선택
3. 조건 설정 (예: 틱데이터 수집 속도 < 10건/초)
4. 알림 채널 설정 (Slack, Email 등)

---

## 문제 해결

### 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker compose logs sub-server

# 컨테이너 상태 확인
docker compose ps -a

# 헬스체크 실패 시
docker compose exec sub-server curl http://localhost:8001/api/status

# 환경 변수 확인
docker compose exec sub-server env | grep KIWOOM
```

### 데이터베이스 연결 오류

```bash
# MariaDB 상태 확인
docker compose exec mariadb mysqladmin -u root -p ping

# 연결 테스트
docker compose exec sub-server python -c "import pymysql; pymysql.connect(host='mariadb', user='kium_user', password='kium_password', database='gslts_trading')"

# 스키마 재생성
docker compose exec mariadb mysql -u root -p gslts_trading < database/schema.sql
```

### Redis 연결 오류

```bash
# Redis 상태 확인
docker compose exec redis redis-cli ping

# 연결 테스트
docker compose exec sub-server python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())"
```

### 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8001
sudo lsof -i :3306

# .env 파일에서 포트 변경
SUB_SERVER_PORT=8002
DB_PORT=3307
```

### 로그 파일 확인

```bash
# Sub Server 로그
docker compose exec sub-server cat /app/logs/sub_server.log

# MariaDB 로그
docker compose exec mariadb cat /var/log/mysql/error.log
```

---

## 프로덕션 배포

### 보안 설정

1. **비밀번호 변경**:
```env
DB_ROOT_PASSWORD=strong_password_here
DB_PASSWORD=strong_password_here
REDIS_PASSWORD=strong_password_here
GRAFANA_PASSWORD=strong_password_here
```

2. **방화벽 설정**:
```bash
# UFW 사용 (Ubuntu)
sudo ufw allow 8001/tcp  # Sub Server API
sudo ufw allow 3000/tcp  # Grafana
sudo ufw deny 3306/tcp   # MariaDB (외부 접근 차단)
sudo ufw deny 6379/tcp   # Redis (외부 접근 차단)
```

3. **HTTPS 설정** (Nginx/Caddy 사용):
```bash
# Nginx Reverse Proxy 예시
sudo apt install nginx certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d yourdomain.com
```

### 성능 최적화

1. **리소스 제한 설정** (docker-compose.yml):
```yaml
services:
  sub-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

2. **로그 로테이션**:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 백업 전략

```bash
# 자동 백업 스크립트 (cron)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# DB 백업
docker compose exec -T mariadb mysqldump -u root -p"$DB_ROOT_PASSWORD" gslts_trading | gzip > backups/db_$DATE.sql.gz

# Redis 백업
docker compose exec redis redis-cli --rdb /data/dump_$DATE.rdb

# 로그 백업
tar -czf backups/logs_$DATE.tar.gz logs/

# 오래된 백업 삭제 (7일)
find backups/ -name "*.gz" -mtime +7 -delete
```

---

## 참고 자료

- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [MariaDB Docker 이미지](https://hub.docker.com/_/mariadb)
- [Redis Docker 이미지](https://hub.docker.com/_/redis)
- [Grafana 공식 문서](https://grafana.com/docs/)
- [Prometheus 공식 문서](https://prometheus.io/docs/)

---

**버전**: 1.0.0
**최종 업데이트**: 2025-11-20
