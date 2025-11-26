"""
종목 관리 서비스

키움 API로 종목 검색 → DB에 동적 등록
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

from main_server.config.settings import get_settings

logger = logging.getLogger(__name__)


class StockService:
    """종목 관리 서비스"""

    def __init__(self):
        self.settings = get_settings()
        self._connection = None

    def _get_connection(self):
        """DB 연결 획득"""
        if self._connection is None or not self._connection.open:
            self._connection = pymysql.connect(
                host=self.settings.DB_HOST,
                port=self.settings.DB_PORT,
                user=self.settings.DB_USER,
                password=self.settings.DB_PASSWORD,
                database=self.settings.DB_NAME,
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=True
            )
        return self._connection

    def register_stock(self, stock_code: str, stock_name: str, market_type: str = "KRX") -> bool:
        """
        종목을 DB에 등록 (없으면 INSERT, 있으면 UPDATE)

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            market_type: 시장구분 (KOSPI, KOSDAQ, ETF)

        Returns:
            bool: 성공 여부
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO stock_master (stock_code, stock_name, market_type, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, 1, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        stock_name = VALUES(stock_name),
                        market_type = VALUES(market_type),
                        is_active = 1,
                        updated_at = NOW()
                """
                cursor.execute(sql, (stock_code, stock_name, market_type))
                logger.info(f"✅ 종목 등록/업데이트: {stock_code} - {stock_name} ({market_type})")
                return True
        except Exception as e:
            logger.error(f"❌ 종목 등록 실패: {stock_code} - {e}")
            return False

    def register_stocks_batch(self, stocks: List[Dict]) -> int:
        """
        여러 종목을 일괄 등록

        Args:
            stocks: [{"stock_code": "005930", "stock_name": "삼성전자", "market_type": "KOSPI"}, ...]

        Returns:
            int: 등록된 종목 수
        """
        count = 0
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO stock_master (stock_code, stock_name, market_type, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, 1, NOW(), NOW())
                    ON DUPLICATE KEY UPDATE
                        stock_name = VALUES(stock_name),
                        market_type = VALUES(market_type),
                        is_active = 1,
                        updated_at = NOW()
                """
                for stock in stocks:
                    cursor.execute(sql, (
                        stock.get('stock_code'),
                        stock.get('stock_name'),
                        stock.get('market_type', 'KRX')
                    ))
                    count += 1
            logger.info(f"✅ 종목 일괄 등록 완료: {count}개")
        except Exception as e:
            logger.error(f"❌ 종목 일괄 등록 실패: {e}")
        return count

    def get_all_stocks(self, market_type: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """
        DB에서 종목 목록 조회

        Args:
            market_type: 시장구분 필터 (None이면 전체)
            active_only: 활성 종목만 조회

        Returns:
            list: 종목 목록
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                sql = "SELECT stock_code, stock_name, market_type, sector FROM stock_master WHERE 1=1"
                params = []

                if active_only:
                    sql += " AND is_active = 1"
                if market_type:
                    sql += " AND market_type = %s"
                    params.append(market_type)

                sql += " ORDER BY stock_code"
                cursor.execute(sql, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ 종목 조회 실패: {e}")
            return []

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        DB에서 종목 검색

        Args:
            keyword: 검색어 (종목코드 또는 종목명)
            limit: 최대 결과 수

        Returns:
            list: 검색 결과
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                sql = """
                    SELECT stock_code, stock_name, market_type, sector
                    FROM stock_master
                    WHERE is_active = 1
                      AND (stock_code LIKE %s OR stock_name LIKE %s)
                    ORDER BY
                        CASE WHEN stock_code = %s THEN 0
                             WHEN stock_code LIKE %s THEN 1
                             WHEN stock_name LIKE %s THEN 2
                             ELSE 3 END,
                        stock_code
                    LIMIT %s
                """
                like_keyword = f"%{keyword}%"
                start_keyword = f"{keyword}%"
                cursor.execute(sql, (like_keyword, like_keyword, keyword, start_keyword, start_keyword, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ 종목 검색 실패: {e}")
            return []

    def get_stock_count(self) -> int:
        """등록된 종목 수 조회"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as cnt FROM stock_master WHERE is_active = 1")
                result = cursor.fetchone()
                return result['cnt'] if result else 0
        except Exception as e:
            logger.error(f"❌ 종목 수 조회 실패: {e}")
            return 0

    def deactivate_stock(self, stock_code: str) -> bool:
        """종목 비활성화"""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE stock_master SET is_active = 0, updated_at = NOW() WHERE stock_code = %s",
                    (stock_code,)
                )
                return True
        except Exception as e:
            logger.error(f"❌ 종목 비활성화 실패: {stock_code} - {e}")
            return False

    def close(self):
        """연결 종료"""
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None


# 서비스 싱글톤
_stock_service: Optional[StockService] = None


def get_stock_service() -> StockService:
    """종목 서비스 싱글톤"""
    global _stock_service
    if _stock_service is None:
        _stock_service = StockService()
    return _stock_service
