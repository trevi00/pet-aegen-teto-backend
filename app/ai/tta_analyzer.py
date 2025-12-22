"""
Test Time Augmentation (TTA)를 사용하는 고급 분석기
예측 시 여러 augmentation을 적용해서 더 안정적이고 정확한 결과를 얻습니다.
"""

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np


class TTAAnalyzer:
    """Test Time Augmentation을 적용한 분석기"""

    def __init__(self, model_path, model_type='efficientnet'):
        """
        TTA 분석기 초기화

        Args:
            model_path: 학습된 모델 파일 경로
            model_type: 'efficientnet' 또는 'resnet50'
        """
        self.model_path = model_path
        self.model_type = model_type
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 기본 transform
        self.base_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        # TTA transforms (5가지 변형)
        self.tta_transforms = [
            # 1. 원본
            transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ]),
            # 2. 수평 뒤집기
            transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.RandomHorizontalFlip(p=1.0),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ]),
            # 3. 밝기 증가
            transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ColorJitter(brightness=0.2),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ]),
            # 4. 약간 회전
            transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.RandomRotation(10),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ]),
            # 5. 확대
            transforms.Compose([
                transforms.Resize((256, 256)),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ]),
        ]

        # 모델 로드
        self.model = None
        self.load_model()

    def load_model(self):
        """모델을 로드합니다"""
        try:
            if self.model_type == 'efficientnet':
                # EfficientNet-B0
                self.model = models.efficientnet_b0(weights=None)
                num_features = self.model.classifier[1].in_features
                self.model.classifier[1] = nn.Linear(num_features, 2)
            elif self.model_type == 'resnet50':
                # ResNet50
                self.model = models.resnet50(pretrained=False)
                num_features = self.model.fc.in_features
                self.model.fc = nn.Linear(num_features, 2)
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")

            # 학습된 가중치 로드
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()

            print(f"✓ {self.model_type.upper()} 모델 로드 완료 (TTA 활성화)")
            return True
        except Exception as e:
            print(f"✗ 모델 로드 실패: {e}")
            self.model = None
            return False

    def is_available(self):
        """모델이 사용 가능한지 확인"""
        return self.model is not None

    def predict_with_tta(self, image_path, num_tta=5):
        """
        TTA를 사용해서 예측합니다

        Args:
            image_path: 이미지 경로
            num_tta: 사용할 TTA 변형 개수 (1-5)

        Returns:
            dict: 예측 결과
        """
        if not self.is_available():
            raise Exception("모델이 로드되지 않았습니다.")

        # 이미지 로드
        image = Image.open(image_path).convert('RGB')

        # 각 TTA transform에 대해 예측
        predictions = []

        with torch.no_grad():
            for i in range(min(num_tta, len(self.tta_transforms))):
                # Transform 적용
                input_tensor = self.tta_transforms[i](image).unsqueeze(0).to(self.device)

                # 예측
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)

                predictions.append(probabilities.cpu().numpy()[0])

        # TTA 결과 평균
        avg_probs = np.mean(predictions, axis=0)

        # 표준편차 (불확실성)
        std_probs = np.std(predictions, axis=0)

        # 최종 예측
        predicted_class = np.argmax(avg_probs)
        classification = 'aegen' if predicted_class == 0 else 'teto'
        confidence = float(avg_probs[predicted_class])

        aegen_prob = float(avg_probs[0])
        teto_prob = float(avg_probs[1])

        # 불확실성 점수 (낮을수록 확신)
        uncertainty = float(np.mean(std_probs))

        return {
            'classification': classification,
            'aegen_score': int(aegen_prob * 10),
            'teto_score': int(teto_prob * 10),
            'confidence': int(confidence * 10),
            'aegen_percentage': aegen_prob * 100,
            'teto_percentage': teto_prob * 100,
            'uncertainty': uncertainty * 100,
            'num_tta': num_tta,
            'description': f'A {"strong and active" if classification == "teto" else "cute and calm"} pet (TTA)',
            'features': {
                'model_type': f'{self.model_type.upper()} with TTA (x{num_tta})',
                'confidence': f'{confidence:.2%}',
                'uncertainty': f'{uncertainty:.2%}'
            }
        }

    def analyze_for_classification(self, image_path):
        """
        BLIP 스타일 인터페이스 (ensemble_analyzer와 호환)
        """
        return self.predict_with_tta(image_path, num_tta=5)


if __name__ == '__main__':
    # 테스트
    print("TTA Analyzer 테스트...")

    try:
        # EfficientNet-B0 모델로 테스트
        analyzer = TTAAnalyzer('trained_model_v3_efficientnet.pth', model_type='efficientnet')

        if analyzer.is_available():
            print("✓ TTA Analyzer가 준비되었습니다!")
            print("  - 5가지 augmentation 적용")
            print("  - 불확실성 측정 가능")
            print("  - 더 안정적이고 정확한 예측")
        else:
            print("✗ 모델을 로드할 수 없습니다.")
    except Exception as e:
        print(f"오류: {e}")
