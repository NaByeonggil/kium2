"""
US Market API 라우터

미국 ETF 섹터 데이터 조회
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from main_server.services.us_market_service import (
    get_us_market_service, US_SECTOR_ETFS, SECTOR_KR_MAPPING
)

router = APIRouter(prefix="/us-market", tags=["US Market"])


@router.get("/sectors")
async def get_all_sectors():
    """
    모든 US 섹터 ETF 데이터 조회

    Returns:
        list: 섹터별 ETF 데이터 (전일 종가 기준)
    """
    service = get_us_market_service()
    return service.get_all_sectors()


@router.get("/sectors/performance")
async def get_sector_performance():
    """
    섹터 성과 요약 (상승/하락 순위)

    Returns:
        dict: 상위 5개 상승/하락 섹터
    """
    service = get_us_market_service()
    return service.get_sector_performance()


@router.get("/sectors/recommended")
async def get_recommended_sectors():
    """
    추천 섹터 (전일 상승률 기준 상위 3개)

    미국 섹터 상승 → 한국 관련 종목 추천
    """
    service = get_us_market_service()
    return service.get_recommended_sectors()


@router.get("/etf/{symbol}")
async def get_etf_data(symbol: str):
    """
    단일 ETF 데이터 조회

    - **symbol**: ETF 티커 (예: XLK, SPY, QQQ)
    """
    service = get_us_market_service()
    data = service.get_etf_data(symbol.upper())

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"ETF {symbol} 데이터를 찾을 수 없습니다"
        )

    return data


@router.get("/sector/{sector_name}")
async def get_sector_with_kr_stocks(sector_name: str):
    """
    섹터별 정보 + 관련 한국 종목

    - **sector_name**: 섹터명 (예: Technology, Healthcare, Financial)

    Returns:
        dict: 섹터 ETF 정보 + 관련 한국 종목 목록
    """
    service = get_us_market_service()
    data = service.get_sector_with_kr_stocks(sector_name)

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"섹터 {sector_name}을(를) 찾을 수 없습니다"
        )

    return data


@router.get("/mapping")
async def get_sector_mapping():
    """
    US → KR 섹터 매핑 정보

    Returns:
        dict: 섹터별 한국 관련 종목 매핑
    """
    return {
        "sectors": SECTOR_KR_MAPPING,
        "etfs": [
            {
                "symbol": etf.symbol,
                "name": etf.name,
                "sector": etf.sector,
                "sector_kr": etf.sector_kr
            }
            for etf in US_SECTOR_ETFS
        ]
    }


@router.get("/etf-list")
async def get_etf_list():
    """
    지원하는 US ETF 목록

    Returns:
        list: ETF 목록
    """
    return [
        {
            "symbol": etf.symbol,
            "name": etf.name,
            "sector": etf.sector,
            "sector_kr": etf.sector_kr
        }
        for etf in US_SECTOR_ETFS
    ]
