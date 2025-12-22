"""
개선된 모델 학습 스크립트 V2
- ResNet50으로 업그레이드 (더 깊고 강력한 모델)
- 571장 데이터셋 사용
- 최적화된 하이퍼파라미터
- Class Weight로 불균형 해소
"""

import sys
import io
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
import os

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


def train_model_v2(dataset_folder, status_dict):
    """
    개선된 모델 학습

    Args:
        dataset_folder: 데이터셋 폴더 경로
        status_dict: 학습 진행 상황 저장 딕셔너리

    Returns:
        dict: 학습 결과
    """

    print("="*60)
    print("개선된 모델 학습 V2 (ResNet50)")
    print("="*60)

    # 디바이스 설정
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"디바이스: {device}")
    status_dict['message'] = f'디바이스: {device}'
    status_dict['progress'] = 5

    # 개선된 데이터 변환
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(30),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.1),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), scale=(0.9, 1.1)),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        # 추가 augmentation
        transforms.RandomGrayscale(p=0.1),
        transforms.RandomApply([transforms.GaussianBlur(3, sigma=(0.1, 2.0))], p=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    # 데이터셋 로드
    print("데이터셋 로딩 중...")
    status_dict['message'] = '데이터셋 로딩 중...'
    status_dict['progress'] = 10

    full_dataset = PetDataset(dataset_folder, transform=train_transform)

    if len(full_dataset) < 10:
        raise ValueError(f"데이터가 부족합니다. 최소 10장 필요 (현재: {len(full_dataset)}장)")

    # 데이터셋 분할 (80% 학습, 20% 검증)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size]
    )

    # 검증 데이터셋에 다른 transform 적용
    val_dataset.dataset.transform = val_transform

    print(f"학습 데이터: {train_size}장, 검증 데이터: {val_size}장")
    status_dict['message'] = f'학습: {train_size}장, 검증: {val_size}장'
    status_dict['progress'] = 15

    # 클래스 가중치 계산 (불균형 해소)
    aegen_count = sum(1 for _, label in full_dataset.samples if label == 0)
    teto_count = sum(1 for _, label in full_dataset.samples if label == 1)
    total_count = aegen_count + teto_count

    class_weights = torch.tensor([
        total_count / (2.0 * aegen_count),
        total_count / (2.0 * teto_count)
    ], device=device)

    print(f"클래스 가중치: 에겐={class_weights[0]:.2f}, 테토={class_weights[1]:.2f}")

    # 데이터 로더 (배치 크기 증가)
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False, num_workers=0)

    # ResNet50 모델 로드 (더 강력한 모델)
    print("ResNet50 모델 로딩 중...")
    status_dict['message'] = 'ResNet50 모델 로딩 중...'
    status_dict['progress'] = 20

    model = models.resnet50(weights='IMAGENET1K_V1')  # pretrained weights

    # 마지막 레이어 교체 (2 클래스 분류)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, 2)

    model = model.to(device)

    # 손실 함수 (클래스 가중치 적용)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # 옵티마이저 (학습률 조정)
    optimizer = optim.AdamW(model.parameters(), lr=0.0001, weight_decay=0.01)

    # Learning Rate Scheduler (더 적극적인 감소)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', patience=5, factor=0.5
    )

    # 학습
    num_epochs = 50  # 더 많은 에폭
    best_acc = 0.0
    patience = 10  # Longer patience
    patience_counter = 0

    print("학습 시작...")
    status_dict['message'] = '학습 시작...'
    status_dict['progress'] = 25

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")
        print("-"*30)

        # 학습 페이즈
        model.train()
        running_loss = 0.0
        running_corrects = 0

        for inputs, labels in train_loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / len(train_dataset)
        epoch_acc = running_corrects.double() / len(train_dataset)

        print(f"학습 Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")

        # 검증 페이즈
        model.eval()
        val_running_corrects = 0

        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)

                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)

                val_running_corrects += torch.sum(preds == labels.data)

        val_acc = val_running_corrects.double() / len(val_dataset)
        print(f"검증 Acc: {val_acc:.4f}")

        # 진행 상황 업데이트
        progress = 25 + int((epoch + 1) / num_epochs * 70)
        status_dict['progress'] = progress
        status_dict['message'] = f'Epoch {epoch + 1}/{num_epochs} - 정확도: {val_acc:.2%}'
        status_dict['log'] = f'Epoch {epoch + 1}: Train Acc {epoch_acc:.2%}, Val Acc {val_acc:.2%}'

        # Learning rate scheduler 업데이트
        scheduler.step(val_acc)

        # 최고 모델 저장 및 Early Stopping
        if val_acc > best_acc:
            best_acc = val_acc
            patience_counter = 0
            torch.save(model.state_dict(), 'trained_model_v2.pth')
            print(f"✓ 최고 모델 저장! (정확도: {val_acc:.4f})")
        else:
            patience_counter += 1
            print(f"  개선 없음 ({patience_counter}/{patience})")

            # Early stopping
            if patience_counter >= patience:
                print(f"\n⚠ Early stopping! {patience} epochs 동안 개선 없음")
                break

    print("\n" + "="*60)
    print(f"학습 완료! 최고 정확도: {best_acc:.2%}")
    print("="*60)

    status_dict['progress'] = 100
    status_dict['message'] = f'학습 완료! 정확도: {best_acc:.2%}'
    status_dict['accuracy'] = f'{best_acc:.2%}'

    return {
        'accuracy': f'{best_acc:.2%}',
        'model_path': 'trained_model_v2.pth',
        'num_epochs': num_epochs,
        'best_val_acc': float(best_acc)
    }


if __name__ == '__main__':
    status = {
        'status': 'training',
        'progress': 0,
        'message': '',
        'log': '',
        'accuracy': 0
    }

    try:
        result = train_model_v2('D:/pet-aegen-teto-dataset', status)
        print("\n학습 결과:", result)
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
