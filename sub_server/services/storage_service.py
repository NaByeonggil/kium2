"""
틱데이터 저장 서비스

DB 연결 및 대량 삽입 처리
"""

import pymysql
from pymysql import Error
from datetime import datetime, date
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TickStorageService:
    """틱데이터 저장 서비스"""

    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'gslts_trading'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

        # 연결 풀 설정
        self.connection = None
        self._ensure_connection()

    def _ensure_connection(self):
        """DB 연결 확인 및 재연결"""
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(**self.db_config)
                logger.info("✅ 데이터베이스 연결 성공")
        except Error as e:
            logger.error(f"❌ DB 연결 실패: {e}")
            raise

    def close(self):
        """DB 연결 종료"""
        if self.connection and self.connection.open:
            self.connection.close()
            logger.info("👋 데이터베이스 연결 종료")

    def bulk_insert_ticks(self, tick_list: List[Dict]) -> int:
        """
        틱데이터 대량 삽입

        Args:
            tick_list: 틱데이터 리스트

        Returns:
            int: 삽입된 행 수
        """
        if not tick_list:
            return 0

        self._ensure_connection()

        sql = """
        INSERT INTO tick_data (
            stock_code, tick_time, price, volume, change_rate,
            high_price, low_price, open_price, accumulated_volume
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = []
        for tick in tick_list:
            tick_time = self._parse_time(tick.get('time', ''))
            values.append((
                tick['stock_code'],
                tick_time,
                tick['price'],
                tick['volume'],
                tick.get('change_rate', 0),
                tick.get('high', 0),
                tick.get('low', 0),
                tick.get('open', 0),
                tick.get('accumulated_volume', 0)
            ))

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(sql, values)
                self.connection.commit()

                inserted_count = cursor.rowcount
                logger.info(f"💾 틱데이터 {inserted_count:,}건 저장 완료")
                return inserted_count

        except Error as e:
            self.connection.rollback()
            logger.error(f"❌ 틱데이터 삽입 실패: {e}")
            raise

    def _parse_time(self, time_str: str) -> datetime:
        """
        HHMMSS 형식을 datetime으로 변환

        Args:
            time_str: HHMMSS 형식 시간 (예: "153045")

        Returns:
            datetime: 오늘 날짜 + 시간
        """
        if not time_str or len(time_str) < 6:
            return datetime.now()

        try:
            today = date.today()
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])

            return datetime(
                today.year, today.month, today.day,
                hour, minute, second
            )
        except (ValueError, IndexError):
            return datetime.now()

    def insert_stock_master(self, stock_code: str, stock_name: str,
                           market_type: str, sector: str = None):
        """
        종목 마스터 등록

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            market_type: 시장구분 (KOSPI, KOSDAQ, ETF)
            sector: 섹터
        """
        self._ensure_connection()

        sql = """
        INSERT INTO stock_master (stock_code, stock_name, market_type, sector)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            stock_name = VALUES(stock_name),
            market_type = VALUES(market_type),
            sector = VALUES(sector),
            updated_at = CURRENT_TIMESTAMP
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (stock_code, stock_name, market_type, sector))
                self.connection.commit()
                logger.debug(f"종목 마스터 등록: {stock_code} - {stock_name}")

        except Error as e:
            self.connection.rollback()
            logger.error(f"❌ 종목 마스터 등록 실패: {e}")

    def insert_trading_volume_rank(self, rank_data: List[Dict]):
        """
        거래대금 랭킹 저장

        Args:
            rank_data: 랭킹 데이터 리스트
        """
        if not rank_data:
            return

        self._ensure_connection()

        sql = """
        INSERT INTO trading_volume_rank (
            stock_code, stock_name, trading_value, rank_position,
            current_price, change_rate, volume, collected_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = [
            (
                item['stock_code'],
                item['stock_name'],
                item['trading_value'],
                item['rank_position'],
                item.get('current_price', 0),
                item.get('change_rate', 0),
                item.get('volume', 0),
                item.get('collected_at', datetime.now())
            )
            for item in rank_data
        ]

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(sql, values)
                self.connection.commit()
                logger.info(f"💾 거래대금 랭킹 {len(values)}건 저장 완료")

        except Error as e:
            self.connection.rollback()
            logger.error(f"❌ 거래대금 랭킹 저장 실패: {e}")

    def get_top_trading_stocks(self, limit: int = 50) -> List[Dict]:
        """
        최신 거래대금 TOP N 종목 조회

        Args:
            limit: 조회할 종목 수

        Returns:
            List[Dict]: 종목 리스트
        """
        self._ensure_connection()

        sql = """
        SELECT stock_code, stock_name, trading_value, rank_position
        FROM trading_volume_rank
        WHERE collected_at = (SELECT MAX(collected_at) FROM trading_volume_rank)
        ORDER BY rank_position
        LIMIT %s
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (limit,))
                results = cursor.fetchall()
                return results

        except Error as e:
            logger.error(f"❌ 거래대금 TOP 종목 조회 실패: {e}")
            return []

    def get_tick_count_today(self) -> int:
        """오늘 수집한 틱데이터 건수 조회"""
        self._ensure_connection()

        sql = """
        SELECT COUNT(*) as count
        FROM tick_data
        WHERE DATE(tick_time) = CURDATE()
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                return result['count'] if result else 0

        except Error as e:
            logger.error(f"❌ 틱데이터 건수 조회 실패: {e}")
            return 0

    def get_database_size(self) -> str:
        """데이터베이스 크기 조회"""
        self._ensure_connection()

        sql = """
        SELECT
            ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
        FROM information_schema.TABLES
        WHERE table_schema = %s
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (self.db_config['database'],))
                result = cursor.fetchone()
                size_mb = result['size_mb'] if result else 0

                if size_mb > 1024:
                    return f"{size_mb / 1024:.2f} GB"
                else:
                    return f"{size_mb:.2f} MB"

        except Error as e:
            logger.error(f"❌ DB 크기 조회 실패: {e}")
            return "Unknown"
