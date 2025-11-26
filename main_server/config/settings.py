"""
Main Server 설정
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 서버 설정
    APP_NAME: str = "GSLTS Main Server"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 키움 API 설정
    KIWOOM_APP_KEY: str = ""
    KIWOOM_SECRET_KEY: str = ""
    KIWOOM_IS_MOCK: bool = True

    # Sub Server 연결
    SUB_SERVER_URL: str = "http://localhost:8001"

    # 데이터베이스 설정
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "kium_user"
    DB_PASSWORD: str = ""
    DB_NAME: str = "gslts_trading"

    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # US Market 데이터 설정
    YAHOO_FINANCE_ENABLED: bool = True
    FINNHUB_API_KEY: Optional[str] = None

    # CORS 설정
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()
