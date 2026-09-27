"""
분석기 진입점. v3 부터는 커스텀 다중 과제 모델 하나로 판정한다.
(v2 까지 섞던 BLIP 은 홀드아웃에서 찍기 수준(51.7%)이고 결과를 50% 쪽으로 끌어당기기만 해서 뺐다.)
이름은 앱 초기화 코드와의 호환을 위해 유지한다.
"""
from app.ai.custom_analyzer import CustomPetAnalyzer
from app.ai.logger import model_logger as logger


class EnsembleAnalyzer:
    def __init__(self) -> None:
        self.custom_analyzer = CustomPetAnalyzer()
        logger.info("[OK] v3 모델 로드 완료 (에겐 비율·닮은 품종·자세)")

    def analyze_for_classification(self, image_path):
        r = self.custom_analyzer.analyze(image_path)
        return {**r, 'ensemble_info': {'model': 'v3'}}
