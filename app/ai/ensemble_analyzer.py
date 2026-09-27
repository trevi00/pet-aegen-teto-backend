"""
앙상블 분석기: BLIP + Custom 모델 결합
두 모델의 예측을 결합하여 더 정확한 결과 도출
"""
from typing import Dict, Any

from app.ai.pet_analyzer import PetAnalyzer
from app.ai.custom_analyzer import CustomPetAnalyzer
from app.config import EnsembleConfig
from app.ai.logger import model_logger as logger


class EnsembleAnalyzer:
    def __init__(self) -> None:
        """앙상블 분석기 초기화"""
        logger.info("앙상블 분석기 초기화 중...")

        # BLIP 모델 로드
        self.blip_analyzer = PetAnalyzer()
        logger.info("[OK] BLIP 모델 로드 완료")

        # 커스텀 모델 로드
        self.custom_analyzer = CustomPetAnalyzer()

        if self.custom_analyzer.is_available():
            self.use_ensemble = True
            logger.info("[OK] 커스텀 모델 로드 완료 - 앙상블 모드 활성화!")
        else:
            self.use_ensemble = False
            logger.warning("[!] 커스텀 모델 없음 - BLIP 단독 모드")

    def analyze_for_classification(self, image_path):
        """
        앙상블 방식으로 이미지를 분석합니다.

        Args:
            image_path: 분석할 이미지 경로

        Returns:
            dict: 앙상블 분석 결과
        """
        if not self.use_ensemble:
            # 커스텀 모델이 없으면 BLIP만 사용
            return self.blip_analyzer.analyze_for_classification(image_path)

        # 1. 두 모델로 각각 분석
        print(f"\n[앙상블 분석] {image_path}")
        print("  [1] BLIP 모델 분석 중...")
        blip_result = self.blip_analyzer.analyze_for_classification(image_path)

        print("  [2] 커스텀 모델 분석 중...")
        custom_result = self.custom_analyzer.analyze_for_classification(image_path)

        # 2. 결과 출력
        print(f"\n  [BLIP 결과]")
        print(f"    - 분류: {blip_result['classification']}")
        print(f"    - 에겐: {blip_result['aegen_score']}/10, 테토: {blip_result['teto_score']}/10")

        print(f"\n  [커스텀 결과]")
        print(f"    - 분류: {custom_result['classification']}")
        print(f"    - 에겐: {custom_result['aegen_percentage']:.1f}%, 테토: {custom_result['teto_percentage']:.1f}%")
        print(f"    - 신뢰도: {custom_result['features']['confidence']}")

        # 3. 앙상블 전략: 가중 평균
        # 커스텀 모델에 더 높은 가중치 (학습된 모델이므로)
        custom_weight = 0.7
        blip_weight = 0.3

        # BLIP 점수를 0-100 퍼센티지로 변환
        blip_total = blip_result['aegen_score'] + blip_result['teto_score']
        blip_aegen_pct = (blip_result['aegen_score'] / blip_total) * 100 if blip_total else 50.0
        blip_teto_pct = 100 - blip_aegen_pct

        # 가중 평균 계산
        final_aegen_pct = (custom_result['aegen_percentage'] * custom_weight +
                          blip_aegen_pct * blip_weight)
        final_teto_pct = (custom_result['teto_percentage'] * custom_weight +
                         blip_teto_pct * blip_weight)

        # 최종 분류 결정
        final_classification = 'aegen' if final_aegen_pct > final_teto_pct else 'teto'

        # 신뢰도 계산 (두 모델의 일치도)
        models_agree = (blip_result['classification'] == custom_result['classification'])
        confidence_bonus = 20 if models_agree else 0

        # 신뢰도: 우세한 클래스의 퍼센티지 + 보너스
        base_confidence = max(final_aegen_pct, final_teto_pct)
        final_confidence = min(100, base_confidence + confidence_bonus)

        print(f"\n  [앙상블 결과]")
        print(f"    - 최종 분류: {final_classification}")
        print(f"    - 에겐: {final_aegen_pct:.1f}%, 테토: {final_teto_pct:.1f}%")
        print(f"    - 신뢰도: {final_confidence:.1f}%")
        print(f"    - 모델 일치: {'YES' if models_agree else 'NO'}")

        # 4. 결과 반환 (BLIP 형식 유지)
        return {
            'classification': final_classification,
            'aegen_score': int(final_aegen_pct / 10),  # 0-10 스케일
            'teto_score': int(final_teto_pct / 10),
            'confidence': int(final_confidence / 10),
            'aegen_percentage': final_aegen_pct,
            'teto_percentage': final_teto_pct,
            'description': blip_result['description'],
            'features': {
                **blip_result['features'],
                'ensemble': {
                    'custom_weight': custom_weight,
                    'blip_weight': blip_weight,
                    'models_agree': models_agree,
                    'confidence': f'{final_confidence:.1f}%',
                    'blip_prediction': blip_result['classification'],
                    'custom_prediction': custom_result['classification'],
                }
            },
            # 앙상블 메타데이터
            'ensemble_info': {
                'blip_aegen': blip_aegen_pct,
                'blip_teto': blip_teto_pct,
                'custom_aegen': custom_result['aegen_percentage'],
                'custom_teto': custom_result['teto_percentage'],
                'models_agree': models_agree,
                'final_confidence': final_confidence,
                'blip_prediction': blip_result['classification'],
                'custom_prediction': custom_result['classification'],
            }
        }

    def get_confidence_level(self, confidence):
        """
        신뢰도 레벨을 반환합니다.

        Args:
            confidence: 신뢰도 점수 (0-100)

        Returns:
            str: 신뢰도 레벨
        """
        if confidence >= 90:
            return "매우 높음"
        elif confidence >= 75:
            return "높음"
        elif confidence >= 60:
            return "보통"
        elif confidence >= 40:
            return "낮음"
        else:
            return "매우 낮음"


if __name__ == '__main__':
    # 테스트
    analyzer = EnsembleAnalyzer()

    print("\n" + "="*60)
    print("앙상블 분석기 테스트")
    print("="*60)

    if analyzer.use_ensemble:
        print("✓ 앙상블 모드 활성화됨")
        print("  - BLIP 가중치: 30%")
        print("  - 커스텀 가중치: 70%")
    else:
        print("⚠ BLIP 단독 모드")
