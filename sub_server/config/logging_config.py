"""
로깅 시스템 설정

파일 로테이션, 레벨별 분리, 색상 출력 지원
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """컬러 포매터 (콘솔 출력용)"""

    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console_color: bool = True
):
    """
    로깅 시스템 초기화

    Args:
        log_dir: 로그 디렉토리 경로
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: 로그 파일 최대 크기 (바이트)
        backup_count: 보관할 로그 파일 개수
        enable_console_color: 콘솔 색상 출력 활성화 여부
    """
    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # 기존 핸들러 제거
    root_logger.handlers.clear()

    # 포맷 설정
    file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # === 1. 콘솔 핸들러 (색상 출력) ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    if enable_console_color:
        console_formatter = ColoredFormatter(console_format, datefmt=date_format)
    else:
        console_formatter = logging.Formatter(console_format, datefmt=date_format)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # === 2. 통합 로그 파일 (크기 기반 로테이션) ===
    all_log_file = log_path / "sub_server.log"
    all_handler = RotatingFileHandler(
        all_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    all_handler.setLevel(logging.DEBUG)
    all_formatter = logging.Formatter(file_format, datefmt=date_format)
    all_handler.setFormatter(all_formatter)
    root_logger.addHandler(all_handler)

    # === 3. 에러 로그 파일 (ERROR 이상만) ===
    error_log_file = log_path / "error.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(file_format, datefmt=date_format)
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    # === 4. 일별 로그 파일 (자정마다 로테이션) ===
    daily_log_file = log_path / f"daily_{datetime.now().strftime('%Y%m%d')}.log"
    daily_handler = TimedRotatingFileHandler(
        daily_log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 30일 보관
        encoding='utf-8'
    )
    daily_handler.setLevel(logging.INFO)
    daily_formatter = logging.Formatter(file_format, datefmt=date_format)
    daily_handler.setFormatter(daily_formatter)
    daily_handler.suffix = "%Y%m%d"
    root_logger.addHandler(daily_handler)

    # === 5. 컴포넌트별 로거 설정 ===
    _setup_component_loggers(log_path, max_bytes, backup_count)

    logging.info("=" * 60)
    logging.info("로깅 시스템 초기화 완료")
    logging.info("=" * 60)
    logging.info(f"로그 디렉토리: {log_path.absolute()}")
    logging.info(f"로그 레벨: {log_level.upper()}")
    logging.info(f"파일 최대 크기: {max_bytes / 1024 / 1024:.1f}MB")
    logging.info(f"백업 파일 개수: {backup_count}개")
    logging.info("")


def _setup_component_loggers(log_path: Path, max_bytes: int, backup_count: int):
    """컴포넌트별 개별 로거 설정"""

    components = {
        'collector': 'sub_server.collectors',
        'api': 'sub_server.api',
        'storage': 'sub_server.services.storage_service',
    }

    file_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    for name, logger_name in components.items():
        logger = logging.getLogger(logger_name)

        # 컴포넌트별 로그 파일
        component_log_file = log_path / f"{name}.log"
        component_handler = RotatingFileHandler(
            component_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        component_handler.setLevel(logging.DEBUG)
        component_formatter = logging.Formatter(file_format, datefmt=date_format)
        component_handler.setFormatter(component_formatter)

        logger.addHandler(component_handler)
        logger.propagate = True  # 루트 로거에도 전파


def get_logger(name: str) -> logging.Logger:
    """
    로거 인스턴스 가져오기

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        logging.Logger: 로거 인스턴스
    """
    return logging.getLogger(name)


# 환경변수에서 로그 설정 읽기
def get_log_config_from_env() -> dict:
    """
    환경변수에서 로그 설정 읽기

    Returns:
        dict: 로그 설정 딕셔너리
    """
    return {
        'log_dir': os.getenv('LOG_DIR', 'logs'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'max_bytes': int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)),
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', 5)),
        'enable_console_color': os.getenv('LOG_CONSOLE_COLOR', 'true').lower() == 'true'
    }
