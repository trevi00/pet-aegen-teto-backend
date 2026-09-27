"""
커스텀 학습된 모델을 사용하는 분석기
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os


class CustomPetAnalyzer:
    def __init__(self, model_path='trained_model_v2.pth'):
        """
        커스텀 학습된 모델을 로드합니다.

        Args:
            model_path: 학습된 모델 파일 경로
        """
        self.model_path = model_path
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        # 온도 보정: 로짓/T 로 과신을 누그러뜨린다 (정확도 불변). 보정값은 학습 후 calibration.json 에서.
        self.temperature = max(float(os.environ.get('MODEL_TEMPERATURE', '1.0')), 1e-3)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        # 모델이 존재하면 로드
        if os.path.exists(model_path):
            self.load_model()
            print(f"커스텀 모델 로드 완료: {model_path}")
        else:
            print(f"커스텀 모델 파일이 없습니다: {model_path}")
            print("기본 BLIP 모델을 사용합니다.")

    def load_model(self):
        """모델을 로드합니다."""
        try:
            # ResNet50 아키텍처 생성
            self.model = models.resnet50(pretrained=False)

            # 마지막 레이어 교체 (2 클래스)
            num_features = self.model.fc.in_features
            self.model.fc = nn.Linear(num_features, 2)

            # 학습된 가중치 로드
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

            return True
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            self.model = None
            return False

    def is_available(self):
        """커스텀 모델이 사용 가능한지 확인"""
        return self.model is not None

    def analyze_for_classification(self, image_path):
        """
        이미지를 분석하여 에겐/테토를 분류합니다.

        Args:
            image_path: 분석할 이미지 파일 경로

        Returns:
            dict: 분석 결과 (classification, confidence 등)
        """
        if not self.is_available():
            raise Exception("커스텀 모델이 로드되지 않았습니다.")

        # 이미지 로드 및 변환
        image = Image.open(image_path).convert('RGB')
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)

        # 예측
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs / self.temperature, dim=1)
            confidence, predicted = torch.max(probabilities, 1)

            # 클래스: 0 = aegen, 1 = teto
            classification = 'aegen' if predicted.item() == 0 else 'teto'
            aegen_prob = probabilities[0][0].item()
            teto_prob = probabilities[0][1].item()

        # BLIP 스타일 결과 형식으로 반환
        return {
            'classification': classification,
            'aegen_score': int(aegen_prob * 10),  # 0-10 스케일
            'teto_score': int(teto_prob * 10),    # 0-10 스케일
            'confidence': int(confidence.item() * 10),
            'aegen_percentage': aegen_prob * 100,
            'teto_percentage': teto_prob * 100,
            'description': f'A {"strong and active" if classification == "aegen" else "cute and calm"} pet',
            'features': {
                'model_type': 'Custom Trained ResNet50',
                'confidence': f'{confidence.item():.2%}'
            }
        }


if __name__ == '__main__':
    # 테스트
    analyzer = CustomPetAnalyzer()

    if analyzer.is_available():
        print("커스텀 모델이 준비되었습니다!")
    else:
        print("커스텀 모델을 사용할 수 없습니다.")
