#!/bin/bash

# ============================================
# GSLTS 트레이딩 시스템 배포 스크립트
# ============================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 로그 출력
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# .env 파일 확인
if [ ! -f ".env" ]; then
    log_warn ".env 파일이 없습니다. .env.example을 복사합니다."
    cp .env.example .env
    log_warn ".env 파일을 수정한 후 다시 실행해주세요."
    exit 1
fi

# 사용법 출력
usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  start       모든 서비스 시작"
    echo "  stop        모든 서비스 중지"
    echo "  restart     모든 서비스 재시작"
    echo "  build       이미지 빌드"
    echo "  logs        로그 확인"
    echo "  status      상태 확인"
    echo "  tools       관리 도구 시작 (phpMyAdmin, Redis Commander)"
    echo "  clean       컨테이너 및 이미지 정리"
    echo "  help        도움말"
    echo ""
}

# 서비스 시작
start() {
    log_info "GSLTS 서비스를 시작합니다..."
    docker compose up -d
    log_info "서비스가 시작되었습니다."
    echo ""
    log_info "접속 주소:"
    echo "  - Frontend:    http://localhost:${FRONTEND_PORT:-80}"
    echo "  - Main API:    http://localhost:${MAIN_SERVER_PORT:-8000}/docs"
    echo "  - Sub Server:  http://localhost:${SUB_SERVER_PORT:-8001}/docs"
    echo "  - Grafana:     http://localhost:${GRAFANA_PORT:-3000}"
    echo "  - Prometheus:  http://localhost:${PROMETHEUS_PORT:-9090}"
}

# 서비스 중지
stop() {
    log_info "GSLTS 서비스를 중지합니다..."
    docker compose down
    log_info "서비스가 중지되었습니다."
}

# 서비스 재시작
restart() {
    stop
    start
}

# 이미지 빌드
build() {
    log_info "Docker 이미지를 빌드합니다..."
    docker compose build --no-cache
    log_info "빌드가 완료되었습니다."
}

# 로그 확인
logs() {
    SERVICE=${2:-}
    if [ -z "$SERVICE" ]; then
        docker compose logs -f
    else
        docker compose logs -f "$SERVICE"
    fi
}

# 상태 확인
status() {
    log_info "서비스 상태:"
    docker compose ps
    echo ""
    log_info "헬스 체크:"
    echo "  Frontend:    $(curl -s http://localhost:${FRONTEND_PORT:-80} > /dev/null && echo "OK" || echo "FAIL")"
    echo "  Main Server: $(curl -s http://localhost:${MAIN_SERVER_PORT:-8000}/health | grep -q healthy && echo "OK" || echo "FAIL")"
    echo "  Sub Server:  $(curl -s http://localhost:${SUB_SERVER_PORT:-8001}/api/status > /dev/null && echo "OK" || echo "FAIL")"
}

# 관리 도구 시작
tools() {
    log_info "관리 도구를 시작합니다..."
    docker compose --profile tools up -d
    log_info "관리 도구가 시작되었습니다."
    echo ""
    log_info "접속 주소:"
    echo "  - phpMyAdmin:      http://localhost:${PHPMYADMIN_PORT:-8080}"
    echo "  - Redis Commander: http://localhost:${REDIS_COMMANDER_PORT:-8081}"
}

# 정리
clean() {
    log_warn "모든 컨테이너와 볼륨을 삭제합니다. 계속하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker compose down -v --rmi all
        log_info "정리가 완료되었습니다."
    else
        log_info "취소되었습니다."
    fi
}

# 메인 로직
case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    build)
        build
        ;;
    logs)
        logs "$@"
        ;;
    status)
        status
        ;;
    tools)
        tools
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
