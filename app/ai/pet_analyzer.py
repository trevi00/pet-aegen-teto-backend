"""
반려동물 이미지 분석 모듈
BLIP Vision 모델을 사용하여 반려동물의 특징을 분석합니다.
"""

from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch


class PetAnalyzer:
    def __init__(self):
        """BLIP 모델 초기화"""
        print("BLIP 모델을 로딩 중...")
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

        # GPU 사용 가능 시 GPU로 이동
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"모델 로딩 완료! (디바이스: {self.device})")

    def analyze_image(self, image_path):
        """
        이미지를 분석하여 반려동물의 특징을 추출합니다.

        Args:
            image_path: 분석할 이미지 파일 경로

        Returns:
            dict: 분석 결과 (description, features)
        """
        # 이미지 로드
        image = Image.open(image_path).convert('RGB')

        # 기본 설명 생성
        inputs = self.processor(image, return_tensors="pt").to(self.device)
        out = self.model.generate(**inputs, max_length=50)
        description = self.processor.decode(out[0], skip_special_tokens=True)

        # 특정 질문으로 더 자세한 정보 추출
        questions = [
            "Does this animal look strong and dignified?",
            "Does this animal look beautiful or cute?",
            "Does this animal look active or energetic?",
            "Does this animal look calm or lazy?",
            "What is the appearance of this animal?"
        ]

        features = {}
        for question in questions:
            inputs = self.processor(image, question, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs, max_length=30)
            answer = self.processor.decode(out[0], skip_special_tokens=True)
            features[question] = answer

        return {
            'description': description,
            'features': features,
            'image_size': image.size
        }

    def analyze_for_classification(self, image_path):
        """
        에겐/테토 분류를 위한 특징 점수를 계산합니다.

        Args:
            image_path: 분석할 이미지 파일 경로

        Returns:
            dict: 분석 결과와 점수
        """
        analysis = self.analyze_image(image_path)

        # 특징 키워드 기반 점수 계산
        aegen_keywords = ['strong', 'dignified', 'powerful', 'active', 'energetic', 'muscular', 'brave']
        teto_keywords = ['cute', 'small', 'soft', 'calm', 'lazy', 'gentle', 'sweet', 'adorable']

        aegen_score = 0
        teto_score = 0

        # 설명 및 특징에서 키워드 추출
        full_text = analysis['description'].lower()
        for feature_text in analysis['features'].values():
            full_text += " " + feature_text.lower()

        # 점수 계산
        for keyword in aegen_keywords:
            if keyword in full_text:
                aegen_score += 1

        for keyword in teto_keywords:
            if keyword in full_text:
                teto_score += 1

        # 결과 반환
        return {
            'description': analysis['description'],
            'features': analysis['features'],
            'aegen_score': aegen_score,
            'teto_score': teto_score,
            'classification': 'aegen' if aegen_score > teto_score else 'teto',
            'confidence': abs(aegen_score - teto_score)
        }


if __name__ == "__main__":
    # 테스트 코드
    analyzer = PetAnalyzer()
    print("Pet Analyzer 초기화 완료!")
