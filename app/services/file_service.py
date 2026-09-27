"""
파일 처리 서비스
파일 업로드, 저장, 검증 등
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FileService:
    """파일 처리 서비스 클래스"""

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    def __init__(self, upload_folder: str):
        """
        Args:
            upload_folder: 파일 업로드 폴더 경로
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)

    def is_allowed_file(self, filename: str) -> bool:
        """
        허용된 파일 확장자인지 확인

        Args:
            filename: 파일명

        Returns:
            허용 여부
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def save_uploaded_file(self, file, original_filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        업로드된 파일 저장

        Args:
            file: 업로드된 파일 객체
            original_filename: 원본 파일명

        Returns:
            (성공 여부, 저장된 경로, 오류 메시지)
        """
        try:
            # 파일 확장자 확인
            if not self.is_allowed_file(original_filename):
                return False, None, '허용되지 않은 파일 형식입니다'

            # 원본 파일명은 쓰지 않는다 — 무작위 이름만 사용
            ext = os.path.splitext(original_filename)[1].lower()
            filepath = os.path.join(self.upload_folder, f"{uuid.uuid4().hex}{ext}")
            file.save(filepath)

            # 확장자만 바꾼 비이미지 파일 거부
            try:
                from PIL import Image
                with Image.open(filepath) as im:
                    im.verify()
            except Exception:
                os.remove(filepath)
                return False, None, '이미지 파일이 아닙니다'

            return True, filepath, None

        except Exception as e:
            logger.error(f"파일 저장 오류: {e}", exc_info=True)
            return False, None, '파일을 처리하지 못했습니다'

    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        오래된 파일 정리

        Args:
            max_age_hours: 최대 보관 시간 (시간)
        """
        try:
            import time
            now = time.time()
            max_age_seconds = max_age_hours * 3600

            for filename in os.listdir(self.upload_folder):
                filepath = os.path.join(self.upload_folder, filename)
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"오래된 파일 삭제: {filepath}")

        except Exception as e:
            logger.error(f"파일 정리 오류: {e}", exc_info=True)
