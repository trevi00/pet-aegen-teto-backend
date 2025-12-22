"""
ResNet50 모델의 정확도 확인 스크립트
"""

import sys
import io
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class PetDataset(Dataset):
    """반려동물 데이터셋"""

    def __init__(self, dataset_folder, transform=None):
        self.samples = []
        self.transform = transform
        self.class_to_idx = {'aegen': 0, 'teto': 1}

        # 데이터 로드
        for class_name in ['aegen', 'teto']:
            class_folder = os.path.join(dataset_folder, class_name)
            if not os.path.exists(class_folder):
                continue

            for img_name in os.listdir(class_folder):
                img_path = os.path.join(class_folder, img_name)
                if os.path.isfile(img_path):
                    self.samples.append((img_path, self.class_to_idx[class_name]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]

        # 이미지 로드
        image = Image.open(img_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        return image, label


def check_model_accuracy_v2():
    """ResNet50 모델 정확도 확인"""
    print("="*60)
    print("ResNet50 모델 정확도 확인")
    print("="*60)

    # 디바이스 설정
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n디바이스: {device}")

    # 데이터 변환
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 데이터셋 로드
    print("\n데이터셋 로딩 중...")
    dataset_folder = 'D:/pet-aegen-teto-dataset'
    dataset = PetDataset(dataset_folder, transform=transform)

    print(f"총 데이터: {len(dataset)}장")

    # 데이터 로더
    dataloader = DataLoader(dataset, batch_size=16, shuffle=False)

    # ResNet50 모델 로드
    print("\nResNet50 모델 로딩 중...")
    model = models.resnet50(pretrained=False)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, 2)

    # 학습된 가중치 로드
    model_path = 'trained_model_v2.pth'
    if not os.path.exists(model_path):
        print(f"✗ 모델 파일이 없습니다: {model_path}")
        return

    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()

    print("✓ ResNet50 모델 로드 완료")

    # 정확도 계산
    print("\n정확도 측정 중...")
    correct = 0
    total = 0
    class_correct = {'aegen': 0, 'teto': 0}
    class_total = {'aegen': 0, 'teto': 0}

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)

            correct += torch.sum(preds == labels.data)
            total += labels.size(0)

            # 클래스별 정확도
            for i in range(labels.size(0)):
                label = labels[i].item()
                pred = preds[i].item()
                class_name = 'aegen' if label == 0 else 'teto'
                class_total[class_name] += 1
                if label == pred:
                    class_correct[class_name] += 1

    # 결과 출력
    accuracy = 100 * correct.double() / total

    print("\n" + "="*60)
    print("📊 ResNet50 정확도 결과")
    print("="*60)
    print(f"\n전체 정확도: {accuracy:.2f}% ({correct}/{total})")

    print(f"\n클래스별 정확도:")
    for class_name in ['aegen', 'teto']:
        class_acc = 100 * class_correct[class_name] / class_total[class_name] if class_total[class_name] > 0 else 0
        print(f"  {class_name}: {class_acc:.2f}% ({class_correct[class_name]}/{class_total[class_name]})")

    print("\n" + "="*60)

    # 이전 모델(ResNet18)과 비교
    print("\n📈 개선 현황:")
    print("  이전 (ResNet18, 210장): 78.10%")
    print(f"  현재 (ResNet50, 571장): {accuracy:.2f}%")
    improvement = accuracy.item() - 78.10
    print(f"  개선: {improvement:+.2f}%p")

    return accuracy.item()


if __name__ == '__main__':
    check_model_accuracy_v2()
