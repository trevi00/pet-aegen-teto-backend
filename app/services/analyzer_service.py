"""
이미지 분석 서비스
AI 모델을 사용한 분석 로직
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AnalyzerService:
    """이미지 분석 서비스 클래스"""
    
    def __init__(self, analyzer=None, classifier=None):
        """
        Args:
            analyzer: 앙상블 분석기 인스턴스
            classifier: 분류기 인스턴스
        """
        self.analyzer = analyzer
        self.classifier = classifier
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        이미지를 분석하고 분류 결과를 반환
        
        Args:
            image_path: 분석할 이미지 경로
            
        Returns:
            분석 결과 딕셔너리
        """
        if not self.analyzer or not self.classifier:
            raise RuntimeError("AI 모델이 로드되지 않았습니다")
        
        try:
            logger.info(f"이미지 분석 시작: {image_path}")
            
            # 1. AI 앙상블 분석
            analysis_result = self.analyzer.analyze_for_classification(image_path)
            logger.info(f"분석 완료: {analysis_result['classification']}")
            
            # 2. 분류 및 코멘트 생성
            classification_result = self.classifier.classify(analysis_result)
            logger.info(f"분류 완료: {classification_result}")
            
            # 3. 신뢰도 정보 추가
            confidence = analysis_result.get('ensemble_info', {}).get('final_confidence', 50)
            models_agree = analysis_result.get('ensemble_info', {}).get('models_agree', False)
            
            return {
                'success': True,
                'classification': classification_result['classification'],
                'comment': classification_result['comment'],
                'aegen_percentage': classification_result['aegen_percentage'],
                'teto_percentage': classification_result['teto_percentage'],
                'confidence': confidence,
                'confidence_level': self._get_confidence_level(confidence),
                'models_agree': models_agree,
                'ensemble_info': analysis_result.get('ensemble_info', {})
            }
            
        except Exception as e:
            logger.error(f"분석 중 오류: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_confidence_level(self, confidence: float) -> str:
        """신뢰도에 따른 레벨 반환"""
        if confidence >= 80:
            return '매우 높음'
        elif confidence >= 60:
            return '높음'
        elif confidence >= 40:
            return '보통'
        else:
            return '낮음'
    
    def is_ready(self) -> bool:
        """모델이 준비되었는지 확인"""
        return self.analyzer is not None and self.classifier is not None
