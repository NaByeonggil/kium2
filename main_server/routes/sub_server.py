"""
Sub Server 연동 API 라우터
"""

from fastapi import APIRouter, HTTPException

from main_server.services.sub_server_client import get_sub_server_client

router = APIRouter(prefix="/sub-server", tags=["Sub Server"])


@router.get("/status")
async def get_sub_server_status():
    """
    Sub Server 상태 조회

    Returns:
        dict: Sub Server 연결 상태 및 상세 정보
    """
    client = get_sub_server_client()
    status = await client.get_status()

    return status


@router.get("/health")
async def check_sub_server_health():
    """
    Sub Server 헬스 체크

    Returns:
        dict: 연결 상태
    """
    client = get_sub_server_client()
    is_healthy = await client.health_check()

    if is_healthy:
        return {"status": "healthy", "connected": True}
    else:
        return {"status": "unhealthy", "connected": False}


@router.get("/collector")
async def get_collector_stats():
    """
    틱 수집기 통계

    Returns:
        dict: 수집 중인 종목 수, 틱 수, 속도 등
    """
    client = get_sub_server_client()
    stats = await client.get_collector_stats()

    return stats


@router.get("/database")
async def get_database_stats():
    """
    데이터베이스 통계

    Returns:
        dict: 오늘 틱 수, DB 크기 등
    """
    client = get_sub_server_client()
    stats = await client.get_database_stats()

    return stats


@router.get("/stocks")
async def get_collecting_stocks():
    """
    수집 중인 종목 목록

    Returns:
        list: 현재 틱데이터 수집 중인 종목
    """
    client = get_sub_server_client()
    stocks = await client.get_collecting_stocks()

    return {"stocks": stocks, "count": len(stocks)}


@router.post("/stocks/add")
async def add_custom_stock(stock_code: str):
    """
    커스텀 종목 추가 (틱 수집 대상)

    - **stock_code**: 종목코드
    """
    client = get_sub_server_client()
    result = await client.add_custom_stock(stock_code)

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "종목 추가 실패")
        )

    return result


@router.post("/stocks/remove")
async def remove_custom_stock(stock_code: str):
    """
    커스텀 종목 제거 (틱 수집 중단)

    - **stock_code**: 종목코드
    """
    client = get_sub_server_client()
    result = await client.remove_custom_stock(stock_code)

    if not result.get("success", False):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "종목 제거 실패")
        )

    return result
