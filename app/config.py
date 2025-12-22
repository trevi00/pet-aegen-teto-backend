"""
애플리케이션 설정 파일
모든 하드코딩된 값들을 중앙 집중화
"""
import os
from typing import Set


# =============================================================================
# 디렉토리 설정
# =============================================================================
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
DATASET_FOLDER = 'D:/pet-aegen-teto-dataset'

# 절대 경로로 변환
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER_ABS = os.path.join(BASE_DIR, UPLOAD_FOLDER)
RESULT_FOLDER_ABS = os.path.join(BASE_DIR, RESULT_FOLDER)


# =============================================================================
# 파일 업로드 설정
# =============================================================================
ALLOWED_EXTENSIONS: Set[str] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


# =============================================================================
# 모델 설정
# =============================================================================
MODEL_PATH = 'trained_model_v2.pth'
MODEL_TYPE = 'resnet50'  # resnet50 또는 efficientnet


# =============================================================================
# 앙상블 설정
# =============================================================================
class EnsembleConfig:
    """앙상블 분석기 설정"""
    CUSTOM_WEIGHT = 0.7  # 커스텀 모델 가중치
    BLIP_WEIGHT = 0.3    # BLIP 모델 가중치
    AGREEMENT_BONUS = 20  # 모델 일치 시 신뢰도 보너스


# =============================================================================
# 서버 설정
# =============================================================================
class ServerConfig:
    """Flask 서버 설정"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000


# =============================================================================
# 로깅 설정
# =============================================================================
class LoggingConfig:
    """로깅 설정"""
    LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_FILE = 'app.log'
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5


# =============================================================================
# 유틸리티 함수
# =============================================================================
def allowed_file(filename: str) -> bool:
    """
    파일 확장자가 허용된 확장자인지 확인

    Args:
        filename: 확인할 파일명

    Returns:
        bool: 허용된 파일이면 True
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_directories() -> None:
    """필요한 디렉토리들을 생성"""
    directories = [
        UPLOAD_FOLDER,
        RESULT_FOLDER,
        DATASET_FOLDER,
        os.path.join(DATASET_FOLDER, 'aegen'),
        os.path.join(DATASET_FOLDER, 'teto')
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
