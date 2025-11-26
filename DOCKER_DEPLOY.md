# GSLTS Docker 배포 가이드

## 시스템 요구사항

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ 디스크 공간

## 빠른 시작

### 1. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 - 키움 API 키 입력
nano .env
```

**필수 설정값:**
```env
KIWOOM_APP_KEY=your_app_key
KIWOOM_SECRET_KEY=your_secret_key
KIWOOM_IS_MOCK=true  # 모의투자
```

### 2. 서비스 시작

```bash
# 배포 스크립트 사용
./scripts/deploy.sh start

# 또는 Docker Compose 직접 사용
docker compose up -d
```

### 3. 접속 확인

| 서비스 | URL | 설명 |
|--------|-----|------|
| Frontend | http://localhost:80 | 트레이딩 대시보드 |
| Main API | http://localhost:8000/docs | 트레이딩 API 문서 |
| Sub Server | http://localhost:8001/docs | 데이터 수집 API 문서 |
| Grafana | http://localhost:3000 | 모니터링 대시보드 |
| Prometheus | http://localhost:9090 | 메트릭 수집기 |

## 배포 스크립트

```bash
# 서비스 시작
./scripts/deploy.sh start

# 서비스 중지
./scripts/deploy.sh stop

# 서비스 재시작
./scripts/deploy.sh restart

# 이미지 빌드 (변경 후)
./scripts/deploy.sh build

# 로그 확인
./scripts/deploy.sh logs
./scripts/deploy.sh logs main-server  # 특정 서비스

# 상태 확인
./scripts/deploy.sh status

# 관리 도구 시작 (phpMyAdmin, Redis Commander)
./scripts/deploy.sh tools

# 전체 정리 (볼륨 포함)
./scripts/deploy.sh clean
```

## 서비스 구성

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (nginx:80)                       │
│                      React Dashboard                        │
└─────────────────────────────┬───────────────────────────────┘
                              │ /api, /ws
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Main Server (FastAPI:8000)                   │
│              Trading API, WebSocket, US Market              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Sub Server (FastAPI:8001)                   │
│              Tick Data Collection, Chart Data               │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│   MariaDB (:3306)       │    │    Redis (:6379)        │
│   Tick Data Storage     │    │   Real-time Cache       │
└─────────────────────────┘    └─────────────────────────┘
```

## 프로덕션 배포

### SSL/HTTPS 설정

1. `frontend/nginx.conf`에 SSL 설정 추가
2. 인증서 볼륨 마운트
3. 80 → 443 리다이렉트

### 보안 설정

```env
# 프로덕션 환경변수
KIWOOM_IS_MOCK=false
DB_PASSWORD=strong_password_here
REDIS_PASSWORD=strong_password_here
GRAFANA_PASSWORD=strong_password_here
```

### 리소스 제한

```yaml
# docker-compose.yml에 추가
services:
  main-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 트러블슈팅

### 서비스가 시작되지 않음
```bash
# 로그 확인
docker compose logs -f

# 컨테이너 상태 확인
docker compose ps -a
```

### 데이터베이스 연결 실패
```bash
# MariaDB 상태 확인
docker compose exec mariadb mysql -u root -p -e "SHOW DATABASES;"

# 네트워크 확인
docker network inspect kium2-network
```

### 프론트엔드 API 연결 실패
```bash
# nginx 설정 확인
docker compose exec frontend cat /etc/nginx/conf.d/default.conf

# API 프록시 테스트
curl http://localhost/api/status
```

## 볼륨 관리

```bash
# 볼륨 목록
docker volume ls | grep kium2

# 볼륨 백업
docker run --rm -v kium2-mariadb-data:/data -v $(pwd):/backup alpine tar cvf /backup/mariadb-backup.tar /data

# 볼륨 복원
docker run --rm -v kium2-mariadb-data:/data -v $(pwd):/backup alpine tar xvf /backup/mariadb-backup.tar -C /
```

## 업데이트

```bash
# 코드 업데이트
git pull

# 이미지 재빌드
./scripts/deploy.sh build

# 서비스 재시작
./scripts/deploy.sh restart
```
