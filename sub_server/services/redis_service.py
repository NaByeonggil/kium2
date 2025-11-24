"""
Redis 캐싱 서비스

실시간 데이터 캐싱, 세션 관리, 메시지 큐
"""

import os
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta

try:
    import redis
    from redis import Redis, ConnectionPool
except ImportError:
    redis = None
    Redis = None
    ConnectionPool = None

logger = logging.getLogger(__name__)


class RedisService:
    """Redis 캐싱 서비스"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: Optional[int] = None,
    ):
        """
        초기화

        Args:
            host: Redis 호스트
            port: Redis 포트
            password: Redis 비밀번호
            db: Redis DB 번호
        """
        if redis is None:
            raise ImportError("redis 패키지가 설치되지 않았습니다. pip install redis")

        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.db = db or int(os.getenv("REDIS_DB", "0"))

        # 연결 풀 생성
        self.pool = ConnectionPool(
            host=self.host,
            port=self.port,
            password=self.password if self.password else None,
            db=self.db,
            decode_responses=True,
            max_connections=50,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )

        self.client: Optional[Redis] = None
        self._connect()

    def _connect(self):
        """Redis 연결"""
        try:
            self.client = Redis(connection_pool=self.pool)
            self.client.ping()
            logger.info(f"✅ Redis 연결 성공: {self.host}:{self.port} (DB: {self.db})")
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            self.client = None

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        if not self.client:
            return False

        try:
            self.client.ping()
            return True
        except:
            return False

    # ============================================
    # 기본 키-값 저장
    # ============================================

    def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """
        값 저장

        Args:
            key: 키
            value: 값 (자동으로 JSON 직렬화)
            expire_seconds: 만료 시간 (초)

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            # JSON 직렬화
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)

            if expire_seconds:
                self.client.setex(key, expire_seconds, value)
            else:
                self.client.set(key, value)

            return True
        except Exception as e:
            logger.error(f"Redis SET 오류 ({key}): {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        값 조회

        Args:
            key: 키
            default: 기본값

        Returns:
            저장된 값 (JSON 자동 역직렬화)
        """
        if not self.client:
            return default

        try:
            value = self.client.get(key)

            if value is None:
                return default

            # JSON 역직렬화 시도
            try:
                return json.loads(value)
            except:
                return value

        except Exception as e:
            logger.error(f"Redis GET 오류 ({key}): {e}")
            return default

    def delete(self, key: str) -> bool:
        """
        키 삭제

        Args:
            key: 키

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE 오류 ({key}): {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        키 존재 여부

        Args:
            key: 키

        Returns:
            존재 여부
        """
        if not self.client:
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS 오류 ({key}): {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """
        만료 시간 설정

        Args:
            key: 키
            seconds: 초

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE 오류 ({key}): {e}")
            return False

    # ============================================
    # 해시 (Hash) 저장
    # ============================================

    def hset(self, name: str, key: str, value: Any) -> bool:
        """
        해시 필드 저장

        Args:
            name: 해시 이름
            key: 필드 키
            value: 값

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)

            self.client.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Redis HSET 오류 ({name}.{key}): {e}")
            return False

    def hget(self, name: str, key: str, default: Any = None) -> Any:
        """
        해시 필드 조회

        Args:
            name: 해시 이름
            key: 필드 키
            default: 기본값

        Returns:
            필드 값
        """
        if not self.client:
            return default

        try:
            value = self.client.hget(name, key)

            if value is None:
                return default

            try:
                return json.loads(value)
            except:
                return value

        except Exception as e:
            logger.error(f"Redis HGET 오류 ({name}.{key}): {e}")
            return default

    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        해시 전체 조회

        Args:
            name: 해시 이름

        Returns:
            해시 데이터
        """
        if not self.client:
            return {}

        try:
            data = self.client.hgetall(name)
            result = {}

            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except:
                    result[key] = value

            return result

        except Exception as e:
            logger.error(f"Redis HGETALL 오류 ({name}): {e}")
            return {}

    def hdel(self, name: str, *keys: str) -> bool:
        """
        해시 필드 삭제

        Args:
            name: 해시 이름
            keys: 삭제할 필드 키들

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            self.client.hdel(name, *keys)
            return True
        except Exception as e:
            logger.error(f"Redis HDEL 오류 ({name}): {e}")
            return False

    # ============================================
    # 리스트 (List) 저장
    # ============================================

    def lpush(self, key: str, *values: Any) -> bool:
        """
        리스트 왼쪽에 추가

        Args:
            key: 키
            values: 값들

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            serialized = []
            for value in values:
                if not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False)
                serialized.append(value)

            self.client.lpush(key, *serialized)
            return True
        except Exception as e:
            logger.error(f"Redis LPUSH 오류 ({key}): {e}")
            return False

    def rpush(self, key: str, *values: Any) -> bool:
        """
        리스트 오른쪽에 추가

        Args:
            key: 키
            values: 값들

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            serialized = []
            for value in values:
                if not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False)
                serialized.append(value)

            self.client.rpush(key, *serialized)
            return True
        except Exception as e:
            logger.error(f"Redis RPUSH 오류 ({key}): {e}")
            return False

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        리스트 범위 조회

        Args:
            key: 키
            start: 시작 인덱스
            end: 끝 인덱스 (-1: 끝까지)

        Returns:
            리스트
        """
        if not self.client:
            return []

        try:
            values = self.client.lrange(key, start, end)
            result = []

            for value in values:
                try:
                    result.append(json.loads(value))
                except:
                    result.append(value)

            return result

        except Exception as e:
            logger.error(f"Redis LRANGE 오류 ({key}): {e}")
            return []

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """
        리스트 자르기 (범위 밖 삭제)

        Args:
            key: 키
            start: 시작 인덱스
            end: 끝 인덱스

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            self.client.ltrim(key, start, end)
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM 오류 ({key}): {e}")
            return False

    # ============================================
    # 틱데이터 전용 메서드
    # ============================================

    def cache_tick_data(
        self,
        stock_code: str,
        tick_data: Dict[str, Any],
        expire_seconds: int = 300
    ) -> bool:
        """
        틱데이터 캐싱

        Args:
            stock_code: 종목코드
            tick_data: 틱데이터
            expire_seconds: 만료 시간 (기본 5분)

        Returns:
            성공 여부
        """
        key = f"tick:{stock_code}:latest"
        return self.set(key, tick_data, expire_seconds)

    def get_cached_tick_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        캐싱된 틱데이터 조회

        Args:
            stock_code: 종목코드

        Returns:
            틱데이터 (없으면 None)
        """
        key = f"tick:{stock_code}:latest"
        return self.get(key)

    def cache_stock_ranking(
        self,
        ranking_data: List[Dict[str, Any]],
        expire_seconds: int = 600
    ) -> bool:
        """
        거래대금 랭킹 캐싱

        Args:
            ranking_data: 랭킹 데이터
            expire_seconds: 만료 시간 (기본 10분)

        Returns:
            성공 여부
        """
        key = "ranking:trading_value"
        return self.set(key, ranking_data, expire_seconds)

    def get_cached_stock_ranking(self) -> Optional[List[Dict[str, Any]]]:
        """
        캐싱된 거래대금 랭킹 조회

        Returns:
            랭킹 데이터 (없으면 None)
        """
        key = "ranking:trading_value"
        return self.get(key)

    def save_custom_stocks(self, stock_info: Dict[str, str]) -> bool:
        """
        사용자가 추가한 커스텀 종목 저장

        Args:
            stock_info: {stock_code: stock_name} 딕셔너리

        Returns:
            성공 여부
        """
        key = "custom_stocks"
        return self.set(key, stock_info)

    def get_custom_stocks(self) -> Dict[str, str]:
        """
        저장된 커스텀 종목 조회

        Returns:
            {stock_code: stock_name} 딕셔너리
        """
        key = "custom_stocks"
        result = self.get(key, {})
        return result if isinstance(result, dict) else {}

    def add_custom_stock(self, stock_code: str, stock_name: str) -> bool:
        """
        커스텀 종목 추가

        Args:
            stock_code: 종목 코드
            stock_name: 종목명

        Returns:
            성공 여부
        """
        stocks = self.get_custom_stocks()
        stocks[stock_code] = stock_name
        return self.save_custom_stocks(stocks)

    def remove_custom_stock(self, stock_code: str) -> bool:
        """
        커스텀 종목 제거

        Args:
            stock_code: 종목 코드

        Returns:
            성공 여부
        """
        stocks = self.get_custom_stocks()
        if stock_code in stocks:
            del stocks[stock_code]
            return self.save_custom_stocks(stocks)
        return False

    # ============================================
    # 유틸리티
    # ============================================

    def flush_db(self) -> bool:
        """
        현재 DB 전체 삭제 (주의!)

        Returns:
            성공 여부
        """
        if not self.client:
            return False

        try:
            self.client.flushdb()
            logger.warning("⚠️ Redis DB 전체 삭제")
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB 오류: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Redis 정보 조회

        Returns:
            Redis 정보
        """
        if not self.client:
            return {}

        try:
            info = self.client.info()
            return {
                "version": info.get("redis_version"),
                "uptime_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": self.client.dbsize(),
            }
        except Exception as e:
            logger.error(f"Redis INFO 오류: {e}")
            return {}

    def close(self):
        """연결 종료"""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis 연결 종료")
            except:
                pass

    def __enter__(self):
        """Context manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close()
