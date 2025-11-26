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


@app.get("/api/stocks")
async def get_collecting_stocks():
    """수집 중인 종목 목록 조회"""
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    return monitoring_service.get_collecting_stocks()


@app.get("/api/stocks/search")
async def search_stocks(q: str = "", limit: int = 20):
    """
    종목 검색

    Query Parameters:
        q: 검색어 (종목명 또는 종목코드)
        limit: 최대 검색 결과 수 (기본값: 20)

    Returns:
        {
            "status": "success",
            "results": [
                {"stock_code": "005930", "stock_name": "삼성전자", "market_type": "KOSPI"},
                ...
            ],
            "count": 10
        }
    """
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    if not monitoring_service.tick_collector:
        return JSONResponse(
            status_code=503,
            content={"error": "Tick collector not initialized"}
        )

    if not q or len(q) < 1:
        return {"status": "success", "results": [], "count": 0}

    try:
        # DB에서 검색
        from sub_server.services.storage_service import TickStorageService
        storage = TickStorageService()
        try:
            results = storage.search_stocks(q.strip(), limit)
            return {
                "status": "success",
                "results": results,
                "count": len(results)
            }
        finally:
            storage.close()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"검색 실패: {str(e)}"}
        )


@app.post("/api/stocks/add")
async def add_stock(request: Request):
    """
    종목 동적 추가

    Request Body:
        {
            "stock_code": "005930",
            "stock_name": "삼성전자" (선택)
        }
    """
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    if not monitoring_service.tick_collector:
        return JSONResponse(
            status_code=503,
            content={"error": "Tick collector not initialized"}
        )

    try:
        data = await request.json()
        stock_code = (data.get('stock_code') or '').strip()
        stock_name = (data.get('stock_name') or '').strip() or None

        if not stock_code:
            return JSONResponse(
                status_code=400,
                content={"error": "stock_code is required"}
            )

        if len(stock_code) != 6 or not stock_code.isdigit():
            return JSONResponse(
                status_code=400,
                content={"error": "stock_code must be 6-digit number"}
            )

        # 종목 추가
        result = monitoring_service.tick_collector.add_stock(stock_code, stock_name)

        status_code = 200 if result['success'] else 400
        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to add stock: {str(e)}"}
        )


@app.delete("/api/stocks/{stock_code}")
async def remove_stock(stock_code: str):
    """
    종목 동적 제거

    Path Parameter:
        stock_code: 종목 코드 (6자리)
    """
    if not monitoring_service:
        return JSONResponse(
            status_code=503,
            content={"error": "Monitoring service not initialized"}
        )

    if not monitoring_service.tick_collector:
        return JSONResponse(
            status_code=503,
            content={"error": "Tick collector not initialized"}
        )

    try:
        if len(stock_code) != 6 or not stock_code.isdigit():
            return JSONResponse(
                status_code=400,
                content={"error": "stock_code must be 6-digit number"}
            )

        # 종목 제거
        result = monitoring_service.tick_collector.remove_stock(stock_code)

        status_code = 200 if result['success'] else 400
        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to remove stock: {str(e)}"}
        )


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

        .stock-list {
            max-height: 400px;
            overflow-y: auto;
            margin-top: 10px;
        }

        .stock-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 12px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            transition: all 0.2s;
        }

        .stock-item:hover {
            background: #e9ecef;
            border-left-color: #764ba2;
            transform: translateX(5px);
        }

        .stock-code {
            font-weight: bold;
            color: #667eea;
            font-family: 'Courier New', monospace;
        }

        .stock-name {
            color: #333;
            font-weight: 500;
        }

        .mode-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 10px;
        }

        .mode-websocket {
            background: #4CAF50;
            color: white;
        }

        .mode-polling {
            background: #FF9800;
            color: white;
        }

        .add-stock-form {
            display: flex;
            gap: 10px;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px dashed #667eea;
        }

        .add-stock-form input {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            transition: border-color 0.2s;
        }

        .add-stock-form input:focus {
            outline: none;
            border-color: #667eea;
        }

        #stock-code-input {
            width: 150px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }

        #stock-name-input {
            flex: 1;
        }

        #add-stock-btn {
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }

        #add-stock-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        #add-stock-btn:active {
            transform: translateY(0);
        }

        #add-stock-message {
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            font-size: 14px;
            font-weight: 500;
            display: none;
        }

        #add-stock-message.success {
            display: block;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        #add-stock-message.error {
            display: block;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .stock-item {
            position: relative;
        }

        .remove-stock-btn {
            padding: 4px 8px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
            transition: background 0.2s;
        }

        .remove-stock-btn:hover {
            background: #c82333;
        }

        /* 검색 관련 스타일 */
        .search-container {
            position: relative;
            flex: 1;
        }

        #stock-search-input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        #stock-search-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }

        .search-results {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .search-results.show {
            display: block;
        }

        .search-result-item {
            padding: 12px 15px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.15s;
        }

        .search-result-item:last-child {
            border-bottom: none;
        }

        .search-result-item:hover {
            background: #f0f4ff;
        }

        .search-result-item.selected {
            background: #e3e9ff;
        }

        .search-result-code {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #667eea;
            margin-right: 10px;
        }

        .search-result-name {
            flex: 1;
            font-weight: 500;
        }

        .search-result-market {
            font-size: 0.85em;
            padding: 3px 8px;
            border-radius: 10px;
            font-weight: bold;
        }

        .search-result-market.kospi {
            background: #e3f2fd;
            color: #1976D2;
        }

        .search-result-market.kosdaq {
            background: #e8f5e9;
            color: #388E3C;
        }

        .search-result-market.etf {
            background: #fff3e0;
            color: #F57C00;
        }

        .selected-stock-info {
            padding: 10px 15px;
            background: #e8f5e9;
            border-radius: 6px;
            margin: 10px 0;
            display: none;
            align-items: center;
            justify-content: space-between;
        }

        .selected-stock-info.show {
            display: flex;
        }

        .selected-stock-info .stock-detail {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .selected-stock-info .clear-btn {
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            font-size: 18px;
            padding: 5px;
        }

        .selected-stock-info .clear-btn:hover {
            color: #dc3545;
        }

        .search-loading {
            padding: 15px;
            text-align: center;
            color: #666;
        }

        .search-no-results {
            padding: 15px;
            text-align: center;
            color: #999;
        }

        /* 시장별 섹션 스타일 */
        .market-section {
            margin: 15px 0;
            border-radius: 8px;
            overflow: hidden;
        }

        .market-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            font-weight: bold;
            color: white;
        }

        .market-label {
            font-size: 1.1em;
        }

        .market-count {
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
        }

        .kospi-section .market-header {
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        }

        .kospi-section .stock-item {
            border-left-color: #2196F3;
        }

        .kosdaq-section .market-header {
            background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
        }

        .kosdaq-section .stock-item {
            border-left-color: #4CAF50;
        }

        .other-section .market-header {
            background: linear-gradient(135deg, #9E9E9E 0%, #757575 100%);
        }

        .other-section .stock-item {
            border-left-color: #9E9E9E;
        }

        .market-section .stock-list {
            max-height: 200px;
            overflow-y: auto;
            background: #f8f9fa;
            padding: 10px;
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

            <!-- 수집 종목 목록 -->
            <div class="card" style="grid-column: span 2;">
                <div class="card-title">📈 수집 종목 목록 <span id="collection-mode-badge"></span></div>

                <!-- 종목 검색/추가 폼 -->
                <div class="add-stock-form">
                    <div class="search-container">
                        <input type="text" id="stock-search-input" placeholder="🔍 종목명 또는 종목코드 검색..." autocomplete="off">
                        <div id="search-results" class="search-results"></div>
                    </div>
                    <button id="add-stock-btn" onclick="addSelectedStock()">➕ 종목 추가</button>
                </div>
                <div id="selected-stock-info" class="selected-stock-info"></div>
                <div id="add-stock-message"></div>

                <div id="stocks-list">로딩 중...</div>
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

        async function fetchStocks() {
            try {
                const response = await fetch('/api/stocks');
                const stocksData = await response.json();
                updateStocks(stocksData);
            } catch (error) {
                console.error('종목 조회 실패:', error);
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

        function updateStocks(stocksData) {
            const stocksDiv = document.getElementById('stocks-list');
            const modeBadge = document.getElementById('collection-mode-badge');

            if (stocksData.status === 'error' || !stocksData.stocks || stocksData.stocks.length === 0) {
                stocksDiv.innerHTML = '<div class="stat-value" style="text-align: center; color: #999;">수집 중인 종목이 없습니다</div>';
                modeBadge.innerHTML = '';
                return;
            }

            // 수집 모드 배지
            const mode = stocksData.collection_mode || 'unknown';
            const modeClass = mode === 'websocket' ? 'mode-websocket' : 'mode-polling';
            const modeText = mode === 'websocket' ? 'WebSocket' : mode === 'polling' ? 'REST API 폴링' : mode;
            modeBadge.innerHTML = `<span class="mode-badge ${modeClass}">${modeText}</span>`;

            // 종목 목록 생성 함수
            const createStockList = (stocks, marketLabel, marketClass) => {
                if (!stocks || stocks.length === 0) return '';

                const stocksHTML = stocks.map(stock => `
                    <div class="stock-item">
                        <div>
                            <span class="stock-code">${stock.stock_code}</span>
                            <span class="stock-name">${stock.stock_name}</span>
                        </div>
                        <button class="remove-stock-btn" onclick="removeStock('${stock.stock_code}')">❌ 제거</button>
                    </div>
                `).join('');

                return `
                    <div class="market-section ${marketClass}">
                        <div class="market-header">
                            <span class="market-label">${marketLabel}</span>
                            <span class="market-count">${stocks.length}개</span>
                        </div>
                        <div class="stock-list">${stocksHTML}</div>
                    </div>
                `;
            };

            // 코스피, 코스닥, 기타 분류
            const kospiHTML = createStockList(stocksData.kospi, '🔵 코스피 (KOSPI)', 'kospi-section');
            const kosdaqHTML = createStockList(stocksData.kosdaq, '🟢 코스닥 (KOSDAQ)', 'kosdaq-section');
            const otherHTML = createStockList(stocksData.other, '⚪ 기타', 'other-section');

            stocksDiv.innerHTML = `
                <div class="stat">
                    <span class="stat-label">총 종목 수</span>
                    <span class="stat-value">${stocksData.stock_count}개 (코스피: ${stocksData.kospi_count || 0}, 코스닥: ${stocksData.kosdaq_count || 0})</span>
                </div>
                ${kospiHTML}
                ${kosdaqHTML}
                ${otherHTML}
            `;
        }

        async function addStock() {
            const codeInput = document.getElementById('stock-code-input');
            const nameInput = document.getElementById('stock-name-input');
            const message = document.getElementById('add-stock-message');
            const btn = document.getElementById('add-stock-btn');

            const stockCode = codeInput.value.trim();
            const stockName = nameInput.value.trim();

            // 유효성 검사
            if (!stockCode) {
                showMessage('종목 코드를 입력해주세요', 'error');
                return;
            }

            if (!/^[0-9]{6}$/.test(stockCode)) {
                showMessage('종목 코드는 6자리 숫자여야 합니다', 'error');
                return;
            }

            // 버튼 비활성화
            btn.disabled = true;
            btn.textContent = '추가 중...';

            try {
                const response = await fetch('/api/stocks/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        stock_code: stockCode,
                        stock_name: stockName || null
                    })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    showMessage(result.message, 'success');
                    codeInput.value = '';
                    nameInput.value = '';
                    // 즉시 종목 목록 갱신
                    fetchStocks();
                } else {
                    showMessage(result.message || result.error || '종목 추가 실패', 'error');
                }
            } catch (error) {
                showMessage('서버 연결 오류: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '➕ 종목 추가';
            }
        }

        async function removeStock(stockCode) {
            if (!confirm(`종목 ${stockCode}를 제거하시겠습니까?`)) {
                return;
            }

            try {
                const response = await fetch(`/api/stocks/${stockCode}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    showMessage(result.message, 'success');
                    // 즉시 종목 목록 갱신
                    fetchStocks();
                } else {
                    showMessage(result.message || result.error || '종목 제거 실패', 'error');
                }
            } catch (error) {
                showMessage('서버 연결 오류: ' + error.message, 'error');
            }
        }

        function showMessage(text, type) {
            const message = document.getElementById('add-stock-message');
            message.textContent = text;
            message.className = type;

            // 3초 후 메시지 자동 숨김
            setTimeout(() => {
                message.className = '';
                message.style.display = 'none';
            }, 3000);
        }

        // ========== 종목 검색 관련 함수 ==========
        let selectedStock = null;
        let searchTimeout = null;

        // 검색 입력 이벤트 핸들러
        document.addEventListener('DOMContentLoaded', function() {
            const searchInput = document.getElementById('stock-search-input');
            const searchResults = document.getElementById('search-results');

            // 입력 이벤트 (디바운스 적용)
            searchInput.addEventListener('input', function() {
                const query = this.value.trim();

                // 디바운스: 300ms 후에 검색 실행
                clearTimeout(searchTimeout);

                if (query.length < 1) {
                    hideSearchResults();
                    return;
                }

                searchTimeout = setTimeout(() => {
                    searchStocks(query);
                }, 300);
            });

            // 포커스 이벤트
            searchInput.addEventListener('focus', function() {
                if (this.value.trim().length >= 1) {
                    searchStocks(this.value.trim());
                }
            });

            // 검색창 외부 클릭 시 결과 숨김
            document.addEventListener('click', function(e) {
                if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                    hideSearchResults();
                }
            });

            // 키보드 네비게이션
            searchInput.addEventListener('keydown', function(e) {
                const items = searchResults.querySelectorAll('.search-result-item');
                const current = searchResults.querySelector('.search-result-item.selected');

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    if (!current && items.length > 0) {
                        items[0].classList.add('selected');
                    } else if (current && current.nextElementSibling) {
                        current.classList.remove('selected');
                        current.nextElementSibling.classList.add('selected');
                    }
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (current && current.previousElementSibling) {
                        current.classList.remove('selected');
                        current.previousElementSibling.classList.add('selected');
                    }
                } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (current) {
                        const code = current.dataset.code;
                        const name = current.dataset.name;
                        const market = current.dataset.market;
                        selectStock(code, name, market);
                    }
                } else if (e.key === 'Escape') {
                    hideSearchResults();
                }
            });
        });

        // 종목 검색 API 호출
        async function searchStocks(query) {
            const searchResults = document.getElementById('search-results');

            // 로딩 표시
            searchResults.innerHTML = '<div class="search-loading">🔍 검색 중...</div>';
            searchResults.classList.add('show');

            try {
                const response = await fetch(`/api/stocks/search?q=${encodeURIComponent(query)}&limit=20`);
                const data = await response.json();

                if (data.status === 'success' && data.results && data.results.length > 0) {
                    displaySearchResults(data.results);
                } else {
                    searchResults.innerHTML = '<div class="search-no-results">검색 결과가 없습니다</div>';
                }
            } catch (error) {
                console.error('검색 오류:', error);
                searchResults.innerHTML = '<div class="search-no-results">검색 중 오류가 발생했습니다</div>';
            }
        }

        // 검색 결과 표시
        function displaySearchResults(results) {
            const searchResults = document.getElementById('search-results');

            const html = results.map(stock => {
                const marketClass = (stock.market_type || 'krx').toLowerCase();
                const marketLabel = stock.market_type || 'KRX';

                return `
                    <div class="search-result-item"
                         data-code="${stock.stock_code}"
                         data-name="${stock.stock_name}"
                         data-market="${marketLabel}"
                         onclick="selectStock('${stock.stock_code}', '${stock.stock_name.replace(/'/g, "\\'")}', '${marketLabel}')">
                        <span class="search-result-code">${stock.stock_code}</span>
                        <span class="search-result-name">${stock.stock_name}</span>
                        <span class="search-result-market ${marketClass}">${marketLabel}</span>
                    </div>
                `;
            }).join('');

            searchResults.innerHTML = html;
            searchResults.classList.add('show');
        }

        // 검색 결과 숨김
        function hideSearchResults() {
            const searchResults = document.getElementById('search-results');
            searchResults.classList.remove('show');
        }

        // 종목 선택
        function selectStock(code, name, market) {
            selectedStock = { code, name, market };

            // 검색창에 선택된 종목 표시
            const searchInput = document.getElementById('stock-search-input');
            searchInput.value = `${code} - ${name}`;

            // 선택된 종목 정보 표시
            const selectedInfo = document.getElementById('selected-stock-info');
            const marketClass = market.toLowerCase();
            selectedInfo.innerHTML = `
                <div class="stock-detail">
                    <span class="stock-code">${code}</span>
                    <span class="stock-name">${name}</span>
                    <span class="search-result-market ${marketClass}">${market}</span>
                </div>
                <button class="clear-btn" onclick="clearSelection()">✕</button>
            `;
            selectedInfo.classList.add('show');

            // 검색 결과 숨김
            hideSearchResults();
        }

        // 선택 취소
        function clearSelection() {
            selectedStock = null;
            document.getElementById('stock-search-input').value = '';
            document.getElementById('selected-stock-info').classList.remove('show');
        }

        // 선택된 종목 추가
        async function addSelectedStock() {
            const btn = document.getElementById('add-stock-btn');

            if (!selectedStock) {
                // 직접 입력된 코드 확인
                const searchInput = document.getElementById('stock-search-input');
                const inputValue = searchInput.value.trim();

                // 6자리 숫자인지 확인
                if (/^[0-9]{6}$/.test(inputValue)) {
                    selectedStock = { code: inputValue, name: null, market: 'KRX' };
                } else {
                    showMessage('종목을 검색하여 선택해주세요', 'error');
                    return;
                }
            }

            // 버튼 비활성화
            btn.disabled = true;
            btn.textContent = '추가 중...';

            try {
                const response = await fetch('/api/stocks/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        stock_code: selectedStock.code,
                        stock_name: selectedStock.name
                    })
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    showMessage(result.message, 'success');
                    clearSelection();
                    // 즉시 종목 목록 갱신
                    fetchStocks();
                } else {
                    showMessage(result.message || result.error || '종목 추가 실패', 'error');
                }
            } catch (error) {
                showMessage('서버 연결 오류: ' + error.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '➕ 종목 추가';
            }
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

            // 수집 모드 배지
            const mode = collector.collection_mode || 'unknown';
            const modeClass = mode === 'websocket' ? 'mode-websocket' : 'mode-polling';
            const modeText = mode === 'websocket' ? 'WebSocket' : mode === 'polling' ? 'REST API 폴링' : mode;

            document.getElementById('collector-stats').innerHTML = `
                <div class="stat">
                    <span class="stat-label">상태</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">수집 모드</span>
                    <span class="mode-badge ${modeClass}">${modeText}</span>
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
        fetchStocks();

        // 5초마다 갱신
        setInterval(() => {
            fetchStatus();
            fetchHealth();
            fetchStocks();
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
