"""
Main Server 메인 엔트리포인트

사용자 트레이딩 인터페이스 서버
- 매매 주문 (매수/매도/정정/취소)
- 호가창 (10호가)
- 종목 검색 및 차트
- 잔고 및 포트폴리오
- US ETF 섹터 데이터
- Sub Server 연동
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from main_server.config.settings import get_settings
from main_server.routes import orderbook, trading, balance, stocks, us_market, kr_market, sub_server, websocket

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # 시작
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("🚀 Main Server 시작")
    logger.info("=" * 60)
    logger.info(f"앱 이름: {settings.APP_NAME}")
    logger.info(f"버전: {settings.APP_VERSION}")
    logger.info(f"모의투자: {settings.KIWOOM_IS_MOCK}")
    logger.info(f"Sub Server: {settings.SUB_SERVER_URL}")
    logger.info("=" * 60)

    yield

    # 종료
    logger.info("=" * 60)
    logger.info("⏹️ Main Server 종료")
    logger.info("=" * 60)


# FastAPI 앱 생성
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## GSLTS Main Server

키움 API 기반 트레이딩 인터페이스

### 주요 기능

- **매매**: 매수/매도/정정/취소 주문
- **호가창**: 10호가 실시간 데이터
- **종목**: 검색, 현재가, 차트
- **잔고**: 계좌 잔고, 보유종목
- **US Market**: 미국 ETF 섹터 데이터
- **Sub Server**: 틱데이터 수집 서버 연동
- **WebSocket**: 실시간 데이터 스트리밍
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 예외 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "서버 내부 오류가 발생했습니다",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# 라우터 등록
app.include_router(orderbook.router, prefix="/api")
app.include_router(trading.router, prefix="/api")
app.include_router(balance.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(us_market.router, prefix="/api")
app.include_router(kr_market.router, prefix="/api")
app.include_router(sub_server.router, prefix="/api")
app.include_router(websocket.router)


# 루트 엔드포인트
@app.get("/")
async def root():
    """서버 정보"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "orderbook": "/api/orderbook/{stock_code}",
            "trading": "/api/trading/order",
            "balance": "/api/balance",
            "stocks": "/api/stocks/search?keyword=",
            "us_market": "/api/us-market/sectors",
            "kr_market": "/api/kr-market/sectors",
            "sub_server": "/api/sub-server/status",
            "websocket": "/ws/price/{stock_code}"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}


@app.get("/api/status")
async def get_status():
    """서버 상태"""
    return {
        "server": "main",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "is_mock": settings.KIWOOM_IS_MOCK,
        "sub_server_url": settings.SUB_SERVER_URL
    }


def main():
    """메인 함수"""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main_server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
