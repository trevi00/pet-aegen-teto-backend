"""에겐테토 v3 모델 정의 — 학습(training/train_multitask.py)과 서비스(custom_analyzer.py)가 같이 쓴다.

ResNet50 몸통 하나에 머리 셋:
  aegen : 로짓 1개, sigmoid → 에겐 확률. 규칙 점수(품종 0.6 + 자세 0.3 + 나이 0.1)를 부드러운 목표로 학습
  breed : 37품종 분류 (닮은 품종 — 코멘트·결과 화면용)
  pose  : 사진 속 자세 회귀, tanh → -1 차분 ~ +1 활발 (CLIP 자세 점수를 목표로 학습)
"""
import torch
import torch.nn as nn
from torchvision import models, transforms

NUM_BREEDS = 37

# 서비스와 평가가 같은 전처리를 쓴다
EVAL_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


class AgttNet(nn.Module):
    def __init__(self, pretrained: bool = False):
        super().__init__()
        weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        self.backbone = models.resnet50(weights=weights)
        dim = self.backbone.fc.in_features
        self.backbone.fc = nn.Identity()
        self.aegen = nn.Linear(dim, 1)
        self.breed = nn.Linear(dim, NUM_BREEDS)
        self.pose = nn.Linear(dim, 1)

    def forward(self, x):
        h = self.backbone(x)
        return self.aegen(h).squeeze(1), self.breed(h), torch.tanh(self.pose(h)).squeeze(1)
