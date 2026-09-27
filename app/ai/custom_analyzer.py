"""
v3 커스텀 모델 분석기 — 에겐 비율·닮은 품종·사진 속 자세를 한 번에 예측한다.
모델 정의는 agtt_net.py, 학습은 training/train_multitask.py.
"""
import json
import os

import torch
from PIL import Image

from app.ai.agtt_net import EVAL_TRANSFORM, AgttNet

_HERE = os.path.dirname(__file__)


class CustomPetAnalyzer:
    def __init__(self, model_path='trained_model_v3.pth', meta_path='model_v3_meta.json',
                 info_path=os.path.join(_HERE, 'breed_info.json')):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        meta = json.load(open(meta_path, encoding='utf-8'))
        self.breeds = meta['breeds']                     # 학습 때의 품종 순서 = breed 머리의 출력 순서
        self.info = json.load(open(info_path, encoding='utf-8'))  # key → {ko, species, known}
        self.model = AgttNet(pretrained=False)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device).eval()

    def is_available(self):
        return self.model is not None

    @torch.no_grad()
    def analyze(self, image_path):
        x = EVAL_TRANSFORM(Image.open(image_path).convert('RGB')).unsqueeze(0).to(self.device)
        a, breed_logits, pose = self.model(x)
        aegen = torch.sigmoid(a)[0].item() * 100
        probs = torch.softmax(breed_logits[0], 0)
        top = probs.topk(3)
        breeds = []
        for p, i in zip(top.values.tolist(), top.indices.tolist()):
            key = self.breeds[i]
            breeds.append({'key': key, 'ko': self.info[key]['ko'], 'prob': p, 'known': self.info[key]['known']})
        cat_prob = sum(p for p, key in zip(probs.tolist(), self.breeds) if self.info[key]['species'] == 'cat')
        return {
            'aegen_percentage': aegen,
            'teto_percentage': 100 - aegen,
            'classification': 'aegen' if aegen >= 50 else 'teto',
            'breeds': breeds,
            'species': 'cat' if cat_prob >= 0.5 else 'dog',
            'pose': pose[0].item(),                      # -1 차분 ~ +1 활발
        }
