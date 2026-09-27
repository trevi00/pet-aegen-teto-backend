"""
로깅 시스템
애플리케이션 전체에서 사용할 통합 로거
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.config import LoggingConfig


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    로거를 설정하고 반환합니다.

    Args:
        name: 로거 이름 (일반적으로 모듈명)
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 콘솔만 출력)

    Returns:
        logging.Logger: 설정된 로거 객체
    """
    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 재설정하지 않음
    if logger.handlers:
        return logger

    # 로그 레벨 설정
    log_level = level or LoggingConfig.LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))

    # 포맷터 설정
    formatter = logging.Formatter(
        LoggingConfig.FORMAT,
        datefmt=LoggingConfig.DATE_FORMAT
    )

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 설정 (선택적)
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=LoggingConfig.MAX_BYTES,
                backupCount=LoggingConfig.BACKUP_COUNT,
                encoding='utf-8'
            )
        except OSError:
            # 읽기 전용 컨테이너 등 — 콘솔 로그만 사용
            file_handler = None
        if file_handler:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


# 앱 전역 로거
app_logger = setup_logger('app', log_file=LoggingConfig.LOG_FILE)
model_logger = setup_logger('model', log_file=LoggingConfig.LOG_FILE)
api_logger = setup_logger('api', log_file=LoggingConfig.LOG_FILE)
