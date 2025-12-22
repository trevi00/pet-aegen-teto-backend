# 반려동물 에겐 vs 테토 AI 분석 시스템

반려동물 사진을 업로드하면 AI가 분석하여 에겐(차분한 성격) 또는 테토(활발한 성격) 유형을 판별하는 백엔드 API 서버입니다.

## 소개

### 에겐(Aegen)이란?
- 차분하고 신중한 성격
- 상황을 관찰하고 천천히 행동함
- 낯선 환경에서 조심스러운 태도
- 독립적이고 자기만의 공간을 중시

### 테토(Teto)란?
- 활발하고 적극적인 성격
- 호기심이 많고 탐험을 즐김
- 새로운 것에 빠르게 반응
- 사교적이고 관심받는 것을 좋아함

## 기술 스택

- AI/ML: PyTorch, torchvision (ResNet50), Transformers (BLIP)
- Backend: Python, Flask, Flask-CORS
- Image Processing: Pillow
- Deployment: Docker, Gunicorn

## AI 모델 구조

앙상블 시스템으로 두 모델의 예측을 결합하여 84.06% 정확도 달성

```
입력 이미지
    |
    +------------------+------------------+
    |                  |                  |
BLIP 모델 (30%)   ResNet50 모델 (70%)   결과 결합
    |                  |                  |
    +------------------+------------------+
                       |
                   신뢰도 계산
                       |
                   최종 결과
```

## 설치 및 실행

### 요구사항

- Python 3.11 이상
- 8GB RAM 이상 권장 (모델 로딩용)

### 로컬 개발 환경

1. 저장소 클론
```bash
git clone https://github.com/trevi00/pet-aegen-teto-backend.git
cd pet-aegen-teto-backend
```

2. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 학습된 모델 파일 준비
```
trained_model_v2.pth 파일을 프로젝트 루트에 배치
(용량 문제로 Git에 포함되지 않음, 별도 다운로드 필요)
```

5. 서버 실행
```bash
python app.py
```

6. 브라우저에서 접속
```
http://localhost:5000
```

### Docker 배포

```bash
docker build -t pet-aegen-teto-backend .
docker run -p 5000:5000 pet-aegen-teto-backend
```

## 프로젝트 구조

```
pet-aegen-teto-backend/
├── app.py                    # Flask 웹 서버 (메인)
├── config.py                 # 중앙 설정 관리
├── logger.py                 # 통합 로깅 시스템
├── app/
│   ├── ensemble_analyzer.py  # 앙상블 분석기 (BLIP + ResNet50)
│   ├── pet_analyzer.py       # BLIP 모델 분석기
│   ├── custom_analyzer.py    # ResNet50 모델 분석기
│   ├── tta_analyzer.py       # Test Time Augmentation
│   ├── classifier.py         # 분류 및 코멘트 생성
│   └── result_generator.py   # 결과 이미지 생성
├── train_model_v2.py         # ResNet50 학습 스크립트
├── check_accuracy_v2.py      # 정확도 검증
├── templates/                # HTML 템플릿
├── static/                   # 정적 파일
├── uploads/                  # 업로드된 이미지
├── results/                  # 분석 결과 이미지
├── requirements.txt          # 의존성 목록
├── Dockerfile                # Docker 설정
└── docker-compose.yml        # Docker Compose 설정
```

## API 명세

### 이미지 분석

```
POST /analyze
Content-Type: multipart/form-data

Request:
  - image: File (PNG, JPG, JPEG, GIF, WEBP)

Response:
{
  "success": true,
  "classification": "aegen",
  "aegen_percentage": 85.3,
  "teto_percentage": 14.7,
  "confidence": 92.1,
  "confidence_level": "매우 높음",
  "models_agree": true,
  "comment": "완벽한 에겐입니다!",
  "result_image": "result_20251103_120000_image.jpg"
}
```

### 헬스 체크

```
GET /health

Response:
{
  "status": "ok",
  "models_loaded": true
}
```

## 트러블슈팅

### 모델 로딩 실패

증상: 서버 시작 시 모델 파일을 찾을 수 없음

해결:
1. trained_model_v2.pth 파일이 프로젝트 루트에 있는지 확인
2. 파일 권한 확인 (읽기 권한 필요)

### 메모리 부족

증상: 서버 시작 시 메모리 오류 발생

해결:
1. 다른 프로그램 종료하여 메모리 확보
2. config.py에서 배치 크기 조정
3. GPU가 없는 경우 CPU 모드로 실행 (속도 저하)

### 포트 충돌

증상: 5000번 포트가 이미 사용 중

해결:
```python
# app.py 마지막 줄 수정
app.run(debug=True, host='0.0.0.0', port=8000)
```

### CORS 오류

증상: 프론트엔드에서 API 호출 시 CORS 에러

해결:
1. Flask-CORS 설치 확인
2. app.py에서 CORS 설정 확인

### 이미지 분석 실패

증상: 특정 이미지에서 분석 오류 발생

해결:
1. 이미지 파일 크기 확인 (최대 16MB)
2. 지원 형식 확인 (PNG, JPG, JPEG, GIF, WEBP)
3. 이미지 파일이 손상되지 않았는지 확인

## 모델 성능

| 모델 | 정확도 | 데이터셋 | 비고 |
|------|--------|----------|------|
| ResNet18 (v1) | 78.10% | 210장 | 초기 모델 |
| ResNet50 (v2) | 84.06% | 571장 | 현재 사용 중 |

## 환경 변수

```
FLASK_ENV=production
FLASK_DEBUG=0
MAX_CONTENT_LENGTH=16777216
```
