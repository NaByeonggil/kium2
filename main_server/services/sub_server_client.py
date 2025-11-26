"""
Sub Server 연동 클라이언트

Sub Server에서 틱데이터, 랭킹 등 조회
"""

import httpx
import logging
from typing import Optional, Dict, List
from datetime import datetime

from main_server.config.settings import get_settings

logger = logging.getLogger(__name__)


class SubServerClient:
    """Sub Server 연동 클라이언트"""

    def __init__(self, base_url: Optional[str] = None):
        """
        초기화

        Args:
            base_url: Sub Server URL (기본: settings에서 가져옴)
        """
        if base_url:
            self.base_url = base_url
        else:
            settings = get_settings()
            self.base_url = settings.SUB_SERVER_URL

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 가져오기"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=10.0
            )
        return self._client

    async def close(self):
        """클라이언트 종료"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ========== Sub Server 상태 ==========

    async def get_status(self) -> Dict:
        """
        Sub Server 상태 조회

        Returns:
            dict: Sub Server 상태 정보
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/status")

            if response.status_code == 200:
                return {
                    "connected": True,
                    "data": response.json()
                }
            else:
                return {
                    "connected": False,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Sub Server 연결 실패: {e}")
            return {
                "connected": False,
                "error": str(e)
            }

    async def health_check(self) -> bool:
        """
        Sub Server 헬스 체크

        Returns:
            bool: 정상 여부
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/health")
            return response.status_code == 200
        except Exception:
            return False

    # ========== 틱데이터 조회 ==========

    async def get_collector_stats(self) -> Dict:
        """
        수집기 통계 조회

        Returns:
            dict: 틱 수집 통계
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/collector")

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_database_stats(self) -> Dict:
        """
        데이터베이스 통계 조회

        Returns:
            dict: DB 통계 (오늘 틱 수, DB 크기 등)
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/database")

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    # ========== 종목 관리 ==========

    async def add_custom_stock(self, stock_code: str) -> Dict:
        """
        커스텀 종목 추가

        Args:
            stock_code: 종목코드

        Returns:
            dict: 결과
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/stocks/add",
                json={"stock_code": stock_code}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def remove_custom_stock(self, stock_code: str) -> Dict:
        """
        커스텀 종목 제거

        Args:
            stock_code: 종목코드

        Returns:
            dict: 결과
        """
        try:
            client = await self._get_client()
            response = await client.post(
                "/api/stocks/remove",
                json={"stock_code": stock_code}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_collecting_stocks(self) -> List[Dict]:
        """
        현재 수집 중인 종목 목록

        Returns:
            list: 수집 중인 종목 목록
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/stocks")

            if response.status_code == 200:
                return response.json().get("stocks", [])
            else:
                return []
        except Exception as e:
            logger.error(f"수집 종목 조회 실패: {e}")
            return []


# 클라이언트 싱글톤
_sub_server_client: Optional[SubServerClient] = None


def get_sub_server_client() -> SubServerClient:
    """Sub Server 클라이언트 싱글톤"""
    global _sub_server_client
    if _sub_server_client is None:
        _sub_server_client = SubServerClient()
    return _sub_server_client
