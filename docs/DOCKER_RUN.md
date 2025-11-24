# 🐳 Docker로 Sub Server 실행 가이드

> Docker Compose를 사용한 전체 시스템 배포 가이드

## 📋 목차

1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [빠른 시작](#빠른-시작)
4. [서비스 구성](#서비스-구성)
5. [관리 명령어](#관리-명령어)
6. [모니터링](#모니터링)
7. [트러블슈팅](#트러블슈팅)

---

## 개요

Docker Compose를 사용하여 다음 서비스를 한 번에 배포합니다:

- **Sub Server**: 틱데이터 수집 서버 (Python FastAPI)
- **MariaDB**: 데이터베이스
- **Redis**: 캐싱 & 실시간 데이터
- **Prometheus**: 메트릭 수집
- **Grafana**: 모니터링 대시보드
- **phpMyAdmin**: DB 관리 도구 (선택사항)
- **Redis Commander**: Redis 관리 도구 (선택사항)

---

## 사전 준비

### 1. Docker 설치

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker

# 설치 확인
docker --version
docker-compose --version
```

### 2. 환경변수 설정

```bash
cd /home/nbg/Desktop/kium2

# .env 파일 확인 및 수정
cp .env.example .env
nano .env
```

**필수 환경변수:**
```bash
# 키움증권 API (필수!)
KIWOOM_APP_KEY=your_app_key_here
KIWOOM_SECRET_KEY=your_secret_key_here
KIWOOM_IS_MOCK=true

# 데이터베이스
DB_ROOT_PASSWORD=secure_root_password
DB_USER=kium_user
DB_PASSWORD=kium_password
DB_NAME=gslts_trading

# Redis
REDIS_PASSWORD=  # 비워두면 비밀번호 없음

# 포트 설정
SUB_SERVER_PORT=8001
DB_PORT=3306
REDIS_PORT=6379
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
PHPMYADMIN_PORT=8080
REDIS_COMMANDER_PORT=8081
```

---

## 빠른 시작

### 1. 전체 시스템 시작 (백그라운드)

```bash
cd /home/nbg/Desktop/kium2

# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f sub-server
```

### 2. 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 서비스 헬스 체크
docker-compose ps sub-server
```

**출력 예시:**
```
NAME                 IMAGE                    STATUS
kium2-sub-server    kium2-sub-server:latest  Up 2 minutes (healthy)
kium2-mariadb       mariadb:10.11             Up 2 minutes (healthy)
kium2-redis         redis:7.2-alpine          Up 2 minutes (healthy)
kium2-prometheus    prom/prometheus:latest    Up 2 minutes
kium2-grafana       grafana/grafana:latest    Up 2 minutes
```

### 3. 서비스 접속

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Sub Server API** | http://localhost:8001/api/status | 실시간 통계 API |
| **Sub Server 대시보드** | http://localhost:8001/dashboard | 웹 모니터링 |
| **Grafana** | http://localhost:3000 | 시각화 대시보드 |
| **Prometheus** | http://localhost:9090 | 메트릭 저장소 |
| **phpMyAdmin** | http://localhost:8080 | DB 관리 (tools) |
| **Redis Commander** | http://localhost:8081 | Redis 관리 (tools) |

**Grafana 기본 로그인:**
- ID: `admin`
- PW: `admin`

---

## 서비스 구성

### 서비스 그룹

#### 1. 핵심 서비스 (기본 시작)
```bash
docker-compose up -d sub-server mariadb redis
```

#### 2. 모니터링 포함
```bash
docker-compose up -d sub-server mariadb redis prometheus grafana
```

#### 3. 관리 도구 포함
```bash
docker-compose --profile tools up -d
```

### 개별 서비스 관리

```bash
# Sub Server만 재시작
docker-compose restart sub-server

# MariaDB만 시작
docker-compose up -d mariadb

# Redis 로그 확인
docker-compose logs -f redis

# Grafana 중지
docker-compose stop grafana
```

---

## 관리 명령어

### 컨테이너 관리

```bash
# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d sub-server

# 서비스 중지
docker-compose stop

# 서비스 재시작
docker-compose restart sub-server

# 서비스 완전 삭제 (데이터 유지)
docker-compose down

# 서비스 + 볼륨 삭제 (데이터 삭제!)
docker-compose down -v

# 이미지 재빌드
docker-compose build --no-cache sub-server

# 이미지 재빌드 + 재시작
docker-compose up -d --build sub-server
```

### 로그 확인

```bash
# 전체 로그 (실시간)
docker-compose logs -f

# Sub Server 로그만
docker-compose logs -f sub-server

# 최근 100줄
docker-compose logs --tail=100 sub-server

# 특정 시간 이후 로그
docker-compose logs --since 2025-01-21T14:00:00 sub-server
```

### 컨테이너 접속

```bash
# Sub Server 컨테이너 쉘 접속
docker-compose exec sub-server bash

# 파이썬 인터프리터 실행
docker-compose exec sub-server python

# MariaDB 접속
docker-compose exec mariadb mysql -u kium_user -p gslts_trading

# Redis CLI 접속
docker-compose exec redis redis-cli
```

### 데이터 백업

```bash
# MariaDB 백업
docker-compose exec mariadb mysqldump -u root -p gslts_trading > backup_$(date +%Y%m%d).sql

# Redis 백업
docker-compose exec redis redis-cli SAVE
docker cp kium2-redis:/data/dump.rdb ./backup_redis_$(date +%Y%m%d).rdb

# 볼륨 백업
docker run --rm \
  -v kium2-mariadb-data:/source \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/mariadb_backup_$(date +%Y%m%d).tar.gz -C /source .
```

---

## 모니터링

### 1. Sub Server API

#### 전체 상태
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
    "buffer_size": 1024,
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

#### 헬스 체크
```bash
curl http://localhost:8001/api/health
```

### 2. Docker 시스템 모니터링

```bash
# 컨테이너 리소스 사용량 (실시간)
docker stats

# 특정 컨테이너만
docker stats kium2-sub-server

# 디스크 사용량
docker system df

# 볼륨 목록
docker volume ls
```

### 3. Grafana 대시보드

1. 브라우저에서 `http://localhost:3000` 접속
2. 로그인: `admin` / `admin`
3. 대시보드 → GSLTS Monitoring

**주요 메트릭:**
- 틱 수집 속도
- DB 저장 속도
- 메모리/CPU 사용량
- WebSocket 연결 상태

---

## 트러블슈팅

### 1. 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs sub-server

# 상세 정보
docker-compose ps
docker inspect kium2-sub-server
```

**일반적인 원인:**
- 환경변수 누락 (`.env` 파일 확인)
- 포트 충돌 (이미 사용 중인 포트)
- 볼륨 권한 문제

### 2. MariaDB 연결 실패

```bash
# MariaDB 헬스 체크
docker-compose exec mariadb mysqladmin -u root -p ping

# 데이터베이스 확인
docker-compose exec mariadb mysql -u root -p -e "SHOW DATABASES;"

# 스키마 재생성
docker-compose exec mariadb mysql -u root -p gslts_trading < database/schema.sql
```

### 3. Sub Server 재시작 반복

```bash
# 로그에서 에러 확인
docker-compose logs --tail=50 sub-server

# 컨테이너 내부 확인
docker-compose exec sub-server bash
cat /app/logs/sub_server.log
```

**일반적인 원인:**
- 키움 API 토큰 발급 실패
- DB 연결 실패
- 메모리 부족

### 4. 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tlnp | grep :8001
sudo lsof -i :8001

# .env에서 포트 변경
SUB_SERVER_PORT=8002
```

### 5. 볼륨 초기화

```bash
# 경고: 모든 데이터 삭제!
docker-compose down -v

# 볼륨 재생성
docker volume create kium2-mariadb-data
docker volume create kium2-redis-data

# 재시작
docker-compose up -d
```

### 6. 이미지 재빌드 필요

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache sub-server

# 재시작
docker-compose up -d sub-server
```

---

## 성능 최적화

### 1. 리소스 제한 설정

`docker-compose.yml`에 추가:
```yaml
services:
  sub-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 512M
```

### 2. MariaDB 최적화

`database/mariadb-config.cnf`에서 설정:
```ini
[mysqld]
innodb_buffer_pool_size = 1G
max_connections = 500
innodb_log_file_size = 256M
```

### 3. Redis 최적화

```yaml
redis:
  command: >
    redis-server
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
```

---

## 프로덕션 배포

### 1. 환경변수 보안

```bash
# .env 파일 권한 설정
chmod 600 .env

# Docker secrets 사용 (Swarm 모드)
echo "your_api_key" | docker secret create kiwoom_app_key -
```

### 2. 자동 재시작 설정

```yaml
services:
  sub-server:
    restart: always  # unless-stopped 대신
```

### 3. 로그 로테이션

```yaml
services:
  sub-server:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 4. 백업 자동화

```bash
# crontab 추가
0 2 * * * cd /home/nbg/Desktop/kium2 && ./scripts/backup.sh
```

---

## 시스템 요구사항

### 최소 사양
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB (SSD 권장)

### 권장 사양
- CPU: 4 cores
- RAM: 8GB
- Disk: 100GB (SSD)

---

## 유용한 명령어 모음

```bash
# 전체 시스템 상태 확인
docker-compose ps && docker stats --no-stream

# 디스크 정리
docker system prune -a --volumes

# 네트워크 확인
docker network inspect kium2-network

# 특정 컨테이너 재시작
docker-compose restart sub-server && docker-compose logs -f sub-server

# 모든 로그를 파일로 저장
docker-compose logs > docker_logs_$(date +%Y%m%d).log
```

---

## 다음 단계

1. **모니터링 설정**: Grafana 대시보드 커스터마이징
2. **알림 설정**: Prometheus Alertmanager 설정
3. **백업 자동화**: 크론잡 설정
4. **Phase 2 진행**: Main Server 배포

---

**버전**: 1.0.0
**최종 업데이트**: 2025-11-21
