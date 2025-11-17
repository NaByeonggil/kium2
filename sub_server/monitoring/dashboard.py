"""
모니터링 대시보드

FastAPI 기반 실시간 모니터링 웹 대시보드
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv

from sub_server.services.monitoring_service import MonitoringService

# 환경변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(
    title="GSLTS Sub Server 모니터링",
    description="24시간 틱데이터 수집 서버 모니터링 대시보드",
    version="1.0.0"
)

# 모니터링 서비스 (전역 변수로 관리)
monitoring_service: MonitoringService = None


def set_tick_collector(tick_collector):
    """
    틱 수집기 설정 (외부에서 주입)

    Args:
        tick_collector: TickCollector 인스턴스
    """
    global monitoring_service
    monitoring_service = MonitoringService(tick_collector)


# === API 엔드포인트 ===

@app.get("/")
async def root():
    """루트 엔드포인트 - 대시보드로 리다이렉트"""
    return {
        "service": "GSLTS Sub Server Monitoring",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/dashboard",
            "api_status": "/api/status",
            "api_health": "/api/health",
            "api_system": "/api/system",
            "api_collector": "/api/collector",
            "api_database": "/api/database"
        }
    }


@app.get("/api/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Monitoring service not initialized"
            }
        )

    health = monitoring_service.get_health_status()
    status_code = 200 if health['is_healthy'] else 503

    return JSONResponse(status_code=status_code, content=health)


@app.get("/api/status")
async def get_status():
    """전체 상태 조회"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    return monitoring_service.get_full_status()


@app.get("/api/system")
async def get_system_info():
    """시스템 정보 조회"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    return monitoring_service.get_system_info()


@app.get("/api/collector")
async def get_collector_stats():
    """수집기 통계 조회"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    return monitoring_service.get_collector_stats()


@app.get("/api/database")
async def get_database_stats():
    """데이터베이스 통계 조회"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    return monitoring_service.get_database_stats()


@app.get("/api/uptime")
async def get_uptime():
    """가동 시간 조회"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    return monitoring_service.get_uptime_info()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """모니터링 대시보드 HTML"""
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GSLTS Sub Server 모니터링</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        .stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }

        .stat:last-child {
            border-bottom: none;
        }

        .stat-label {
            color: #666;
            font-weight: 500;
        }

        .stat-value {
            color: #333;
            font-weight: bold;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }

        .status-running {
            background: #4CAF50;
            color: white;
        }

        .status-stopped {
            background: #f44336;
            color: white;
        }

        .status-healthy {
            background: #4CAF50;
            color: white;
        }

        .status-unhealthy {
            background: #f44336;
            color: white;
        }

        .progress-bar {
            width: 100%;
            height: 20px;
            background: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }

        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }

        .last-update {
            color: #ddd;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .updating {
            animation: pulse 1s infinite;
        }

        .issue {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 GSLTS Sub Server 모니터링</h1>

        <div class="grid">
            <!-- 헬스 상태 -->
            <div class="card">
                <div class="card-title">💚 헬스 상태</div>
                <div id="health-status">로딩 중...</div>
            </div>

            <!-- 가동 시간 -->
            <div class="card">
                <div class="card-title">⏱️ 가동 시간</div>
                <div id="uptime-info">로딩 중...</div>
            </div>

            <!-- 수집 통계 -->
            <div class="card">
                <div class="card-title">📊 수집 통계</div>
                <div id="collector-stats">로딩 중...</div>
            </div>

            <!-- 데이터베이스 -->
            <div class="card">
                <div class="card-title">💾 데이터베이스</div>
                <div id="database-stats">로딩 중...</div>
            </div>

            <!-- 시스템 리소스 -->
            <div class="card">
                <div class="card-title">🖥️ 시스템 리소스</div>
                <div id="system-info">로딩 중...</div>
            </div>
        </div>

        <div class="refresh-info">
            <span class="last-update" id="last-update">마지막 업데이트: -</span>
            <br>
            <small>5초마다 자동 갱신</small>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
                document.getElementById('last-update').textContent =
                    `마지막 업데이트: ${data.timestamp}`;
            } catch (error) {
                console.error('상태 조회 실패:', error);
            }
        }

        async function fetchHealth() {
            try {
                const response = await fetch('/api/health');
                const health = await response.json();
                updateHealth(health);
            } catch (error) {
                console.error('헬스 체크 실패:', error);
            }
        }

        function updateHealth(health) {
            const healthDiv = document.getElementById('health-status');
            const statusClass = health.is_healthy ? 'status-healthy' : 'status-unhealthy';
            const statusText = health.is_healthy ? '정상' : '주의 필요';

            let issuesHTML = '';
            if (health.issues && health.issues.length > 0) {
                issuesHTML = health.issues.map(issue =>
                    `<div class="issue">⚠️ ${issue}</div>`
                ).join('');
            }

            healthDiv.innerHTML = `
                <div class="stat">
                    <span class="stat-label">상태</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                ${issuesHTML}
            `;
        }

        function updateDashboard(data) {
            // 가동 시간
            document.getElementById('uptime-info').innerHTML = `
                <div class="stat">
                    <span class="stat-label">시작 시간</span>
                    <span class="stat-value">${data.uptime.start_time}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">가동 시간</span>
                    <span class="stat-value">${data.uptime.uptime_formatted}</span>
                </div>
            `;

            // 수집 통계
            const collector = data.collector;
            const statusClass = collector.is_running ? 'status-running' : 'status-stopped';
            const statusText = collector.is_running ? '실행 중' : '중지';

            document.getElementById('collector-stats').innerHTML = `
                <div class="stat">
                    <span class="stat-label">상태</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">총 수집</span>
                    <span class="stat-value">${collector.tick_count?.toLocaleString() || 0}건</span>
                </div>
                <div class="stat">
                    <span class="stat-label">수집 속도</span>
                    <span class="stat-value">${collector.ticks_per_second?.toFixed(1) || 0}건/초</span>
                </div>
                <div class="stat">
                    <span class="stat-label">버퍼 사용률</span>
                    <span class="stat-value">${collector.buffer_usage_percent?.toFixed(1) || 0}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${collector.buffer_usage_percent || 0}%">
                        ${collector.buffer_size?.toLocaleString() || 0}건
                    </div>
                </div>
                <div class="stat">
                    <span class="stat-label">수집 종목</span>
                    <span class="stat-value">${collector.stock_count || 0}개</span>
                </div>
            `;

            // 데이터베이스
            document.getElementById('database-stats').innerHTML = `
                <div class="stat">
                    <span class="stat-label">오늘 저장</span>
                    <span class="stat-value">${data.database.tick_count_today?.toLocaleString() || 0}건</span>
                </div>
                <div class="stat">
                    <span class="stat-label">DB 크기</span>
                    <span class="stat-value">${data.database.database_size || 'Unknown'}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">상태</span>
                    <span class="stat-value">${data.database.status || 'Unknown'}</span>
                </div>
            `;

            // 시스템 정보
            const sys = data.system;
            document.getElementById('system-info').innerHTML = `
                <div class="stat">
                    <span class="stat-label">CPU 사용률</span>
                    <span class="stat-value">${sys.cpu_percent?.toFixed(1) || 0}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${sys.cpu_percent || 0}%">
                        ${sys.cpu_percent?.toFixed(1) || 0}%
                    </div>
                </div>
                <div class="stat">
                    <span class="stat-label">메모리 사용</span>
                    <span class="stat-value">${sys.memory_used_gb?.toFixed(2) || 0} / ${sys.memory_total_gb?.toFixed(2) || 0} GB</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${sys.memory_percent || 0}%">
                        ${sys.memory_percent?.toFixed(1) || 0}%
                    </div>
                </div>
                <div class="stat">
                    <span class="stat-label">디스크 사용</span>
                    <span class="stat-value">${sys.disk_used_gb?.toFixed(2) || 0} / ${sys.disk_total_gb?.toFixed(2) || 0} GB</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${sys.disk_percent || 0}%">
                        ${sys.disk_percent?.toFixed(1) || 0}%
                    </div>
                </div>
            `;
        }

        // 초기 로드
        fetchStatus();
        fetchHealth();

        // 5초마다 갱신
        setInterval(() => {
            fetchStatus();
            fetchHealth();
        }, 5000);
    </script>
</body>
</html>
    """


def run_dashboard(host: str = "0.0.0.0", port: int = 8001):
    """
    대시보드 서버 실행

    Args:
        host: 호스트 주소
        port: 포트 번호
    """
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # 독립 실행 시
    monitoring_service = MonitoringService()
    run_dashboard()
