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

    def get_stock_market_types(self, stock_codes: List[str]) -> Dict[str, str]:
        """
        종목들의 시장 구분 조회

        Args:
            stock_codes: 종목코드 리스트

        Returns:
            dict: {종목코드: 시장구분} (KOSPI, KOSDAQ, ETF, KRX 등)
        """
        if not stock_codes:
            return {}

        self._ensure_connection()

        # IN 절을 위한 플레이스홀더 생성
        placeholders = ', '.join(['%s'] * len(stock_codes))
        sql = f"""
        SELECT stock_code, market_type
        FROM stock_master
        WHERE stock_code IN ({placeholders})
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, stock_codes)
                results = cursor.fetchall()
                return {row['stock_code']: row['market_type'] for row in results}
        except Error as e:
            logger.error(f"❌ 시장 구분 조회 실패: {e}")
            return {}

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

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        종목 검색 (종목명 또는 종목코드로 검색)

        Args:
            keyword: 검색어 (종목명 또는 종목코드)
            limit: 최대 결과 수

        Returns:
            List[Dict]: 검색된 종목 리스트
        """
        if not keyword:
            return []

        self._ensure_connection()

        sql = """
        SELECT stock_code, stock_name, market_type
        FROM stock_master
        WHERE stock_code LIKE %s OR stock_name LIKE %s
        ORDER BY
            CASE
                WHEN stock_code = %s THEN 0
                WHEN stock_code LIKE %s THEN 1
                WHEN stock_name = %s THEN 2
                WHEN stock_name LIKE %s THEN 3
                ELSE 4
            END,
            stock_name
        LIMIT %s
        """

        search_pattern = f"%{keyword}%"
        starts_with = f"{keyword}%"

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (
                    search_pattern,  # stock_code LIKE
                    search_pattern,  # stock_name LIKE
                    keyword,         # exact stock_code match
                    starts_with,     # stock_code starts with
                    keyword,         # exact stock_name match
                    starts_with,     # stock_name starts with
                    limit
                ))
                results = cursor.fetchall()
                return results

        except Error as e:
            logger.error(f"❌ 종목 검색 실패: {e}")
            return []

    def get_all_stocks(self) -> List[Dict]:
        """
        모든 종목 조회

        Returns:
            List[Dict]: 전체 종목 리스트
        """
        self._ensure_connection()

        sql = """
        SELECT stock_code, stock_name, market_type
        FROM stock_master
        ORDER BY stock_name
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                return results

        except Error as e:
            logger.error(f"❌ 전체 종목 조회 실패: {e}")
            return []

    def init_stock_master(self):
        """
        주요 종목 마스터 데이터 초기화
        서버 시작 시 호출하여 기본 종목 데이터를 DB에 저장
        """
        # 주요 코스피 종목
        kospi_stocks = {
            '005930': '삼성전자', '000660': 'SK하이닉스', '035420': 'NAVER', '005380': '현대차', '051910': 'LG화학',
            '006400': '삼성SDI', '035720': '카카오', '068270': '셀트리온', '207940': '삼성바이오로직스', '005490': 'POSCO홀딩스',
            '003670': '포스코퓨처엠', '000270': '기아', '105560': 'KB금융', '028260': '삼성물산', '055550': '신한지주',
            '012330': '현대모비스', '066570': 'LG전자', '003550': 'LG', '096770': 'SK이노베이션', '032830': '삼성생명',
            '017670': 'SK텔레콤', '034730': 'SK', '009150': '삼성전기', '018260': '삼성에스디에스', '086790': '하나금융지주',
            '015760': '한국전력', '010130': '고려아연', '033780': 'KT&G', '011200': 'HMM', '010950': 'S-Oil',
            '009540': '한국조선해양', '000810': '삼성화재', '036570': '엔씨소프트', '024110': '기업은행', '004020': '현대제철',
            '010140': '삼성중공업', '002790': '아모레퍼시픽', '034020': '두산에너빌리티', '047050': '포스코인터내셔널', '090430': '아모레G',
            '326030': 'SK바이오팜', '003490': '대한항공', '000100': '유한양행', '011070': 'LG이노텍', '036460': '한국가스공사',
            '316140': '우리금융지주', '161390': '한국타이어앤테크놀로지', '259960': '크래프톤', '030200': 'KT', '352820': '하이브',
            '071050': '한국금융지주', '097950': 'CJ제일제당', '010620': '현대건설', '251270': '넷마블', '180640': '한진칼',
            '004170': '신세계', '000720': '현대건설', '003410': '쌍용C&E', '021240': '코웨이', '008930': '한미사이언스',
            '016360': '삼성증권', '138040': '메리츠금융지주', '139480': '이마트', '009830': '한화솔루션', '047810': '한국항공우주',
            '042660': '한화오션', '060250': 'NHN KCP', '373220': 'LG에너지솔루션', '000880': '한화', '001570': '금양',
            '000270': '기아', '020150': '롯데에너지머티리얼즈', '006800': '미래에셋증권', '323410': '카카오뱅크', '112610': '씨에스윈드',
        }

        # 주요 코스닥 종목
        kosdaq_stocks = {
            '247540': '에코프로비엠', '086520': '에코프로', '091990': '셀트리온헬스케어', '035760': 'CJ ENM', '293490': '카카오게임즈',
            '041510': '에스엠', '028300': 'HLB', '112040': '위메이드', '145020': '휴젤', '196170': '알테오젠',
            '215600': '신라젠', '357780': '솔루스첨단소재', '039030': '이오테크닉스', '263750': '펄어비스', '403870': 'HPSP',
            '095340': 'ISC', '058610': '어스바이오', '096530': '씨젠', '277810': '레인보우로보틱스', '072770': '율촌화학',
            '038390': '레드캡투어', '067310': '하나마이크론', '064760': '티씨케이', '352480': '씨앤씨인터내셔널', '950210': '프레스티지바이오파마',
            '140860': '파크시스템스', '340570': '티앤엘', '417500': '엔켐', '039440': '에스티아이', '323280': '태성',
            '226330': '신테카바이오', '460850': '파두', '060310': '3S', '014620': '성광벤드', '078140': '대봉엘에스',
            '032640': 'LG유플러스', '086900': '메디톡스', '048410': '현대바이오', '299660': '삼기이브이', '228760': '지노믹트리',
            '114190': '강원에너지', '222080': '씨아이에스', '317530': '캐리소프트', '041020': '폴라리스오피스', '214450': '파마리서치',
            '083310': '엘오티베큠', '222800': '심텍', '035900': 'JYP Ent.', '122870': '와이지엔터테인먼트', '241560': '두산퓨얼셀',
            '131970': '두산테스나', '078600': '대주전자재료', '298380': 'ABL바이오', '141080': '레고켐바이오', '237690': '에스티팜',
        }

        try:
            self._ensure_connection()

            count = 0
            # 코스피 종목 저장
            for code, name in kospi_stocks.items():
                self.insert_stock_master(code, name, 'KOSPI')
                count += 1

            # 코스닥 종목 저장
            for code, name in kosdaq_stocks.items():
                self.insert_stock_master(code, name, 'KOSDAQ')
                count += 1

            logger.info(f"✅ 주요 종목 마스터 데이터 초기화 완료: {count}개")
            return count

        except Error as e:
            logger.error(f"❌ 종목 마스터 초기화 실패: {e}")
            return 0
