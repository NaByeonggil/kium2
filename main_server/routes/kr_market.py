"""
KR Market API 라우터

한국 ETF 섹터 데이터 조회
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from main_server.services.kr_market_service import (
    get_kr_market_service, KR_SECTOR_ETFS, SECTOR_STOCKS, KRMarketService
)
from main_server.api.kiwoom_trading_client import KiwoomTradingClient
from main_server.config.settings import get_settings

router = APIRouter(prefix="/kr-market", tags=["KR Market"])

# 클라이언트 싱글톤
_trading_client: Optional[KiwoomTradingClient] = None


def get_trading_client() -> KiwoomTradingClient:
    """트레이딩 클라이언트 의존성"""
    global _trading_client
    if _trading_client is None:
        settings = get_settings()
        _trading_client = KiwoomTradingClient(
            appkey=settings.KIWOOM_APP_KEY,
            secretkey=settings.KIWOOM_SECRET_KEY,
            is_mock=settings.KIWOOM_IS_MOCK
        )
    return _trading_client


def get_service_with_client() -> KRMarketService:
    """키움 클라이언트가 설정된 서비스 반환"""
    service = get_kr_market_service()
    client = get_trading_client()
    service.set_kiwoom_client(client)
    return service


@router.get("/sectors")
async def get_all_sectors():
    """
    모든 KR 섹터 ETF 데이터 조회

    Returns:
        list: 섹터별 ETF 데이터
    """
    service = get_service_with_client()
    return service.get_all_sectors()


@router.get("/sectors/performance")
async def get_sector_performance():
    """
    섹터 성과 요약 (상승/하락 순위)

    Returns:
        dict: 상위 5개 상승/하락 섹터
    """
    service = get_service_with_client()
    return service.get_sector_performance()


@router.get("/sectors/categories")
async def get_sectors_by_category():
    """
    카테고리별 섹터 분류

    Returns:
        dict: 카테고리별 ETF 분류 (지수, 반도체, 산업재 등)
    """
    service = get_service_with_client()
    return service.get_sectors_by_category()


@router.get("/etf/{code}")
async def get_etf_data(code: str):
    """
    단일 ETF 데이터 조회

    - **code**: ETF 종목코드 (예: 069500, 091160)
    """
    service = get_service_with_client()
    data = service.get_etf_data(code)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"ETF {code} 데이터를 찾을 수 없습니다"
        )

    return data


@router.get("/etf-list")
async def get_etf_list():
    """
    지원하는 KR ETF 목록

    Returns:
        list: ETF 목록
    """
    return [
        {
            "code": etf.code,
            "name": etf.name,
            "sector": etf.sector,
            "sector_kr": etf.sector_kr
        }
        for etf in KR_SECTOR_ETFS
    ]


@router.get("/mapping")
async def get_sector_mapping():
    """
    섹터별 관련 종목 매핑 정보

    Returns:
        dict: 섹터별 관련 종목 매핑
    """
    return {
        "sectors": SECTOR_STOCKS,
        "etfs": [
            {
                "code": etf.code,
                "name": etf.name,
                "sector": etf.sector,
                "sector_kr": etf.sector_kr
            }
            for etf in KR_SECTOR_ETFS
        ]
    }
