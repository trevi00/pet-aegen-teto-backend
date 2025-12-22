"""
API 요청/응답 스키마 정의
Pydantic 사용
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# 분석 관련 스키마
# ============================================================================

class AnalysisResponse(BaseModel):
    """이미지 분석 응답 스키마"""
    success: bool
    classification: str = Field(..., description="분류 결과: 'aegen' 또는 'teto'")
    comment: str = Field(..., description="분석 코멘트")
    aegen_percentage: float = Field(..., ge=0, le=100, description="에겐 퍼센티지")
    teto_percentage: float = Field(..., ge=0, le=100, description="테토 퍼센티지")
    confidence: Optional[float] = Field(None, ge=0, le=100, description="신뢰도")
    confidence_level: Optional[str] = Field(None, description="신뢰도 레벨")
    models_agree: Optional[bool] = Field(None, description="모델 일치 여부")
    ensemble_info: Optional[Dict[str, Any]] = Field(None, description="앙상블 정보")
    error: Optional[str] = Field(None, description="오류 메시지")


class HealthCheckResponse(BaseModel):
    """서버 헬스 체크 응답 스키마"""
    status: str
    models_loaded: bool


# ============================================================================
# 데이터셋 관련 스키마
# ============================================================================

class DatasetInfoResponse(BaseModel):
    """데이터셋 정보 응답 스키마"""
    success: bool
    aegen: int
    teto: int
    total: int
    error: Optional[str] = None


class UploadDatasetResponse(BaseModel):
    """데이터셋 업로드 응답 스키마"""
    success: bool
    saved: int
    message: str
    error: Optional[str] = None


# ============================================================================
# 학습 관련 스키마
# ============================================================================

class TrainingStatus(BaseModel):
    """학습 상태 스키마"""
    status: str = Field(..., description="idle, training, completed, error")
    progress: int = Field(0, ge=0, le=100)
    message: str = ""
    log: str = ""
    accuracy: float = 0.0


class TrainingStartResponse(BaseModel):
    """학습 시작 응답 스키마"""
    success: bool
    message: str
    error: Optional[str] = None
