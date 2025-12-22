# 배포 가이드

반려동물 에겐 vs 테토 분류 시스템 프로덕션 배포 가이드입니다.

## 사전 요구사항

- Docker 및 Docker Compose 설치
- 학습된 모델 파일: `best_model_aegen_teto_ensemble.pth`
- 최소 4GB RAM, 2 CPU 코어

## Docker Compose로 배포 (권장)

### 1. 환경 변수 설정 (선택사항)

```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정 변경
```

### 2. 컨테이너 빌드 및 실행

```bash
# 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f web

# 상태 확인
docker-compose ps
```

### 3. 서비스 접속

- 웹 애플리케이션: http://localhost:5000
- 헬스체크: http://localhost:5000/health

### 4. 중지 및 재시작

```bash
# 중지
docker-compose down

# 재시작
docker-compose restart

# 재빌드 (코드 변경 시)
docker-compose up -d --build
```

## Docker만 사용하여 배포

### 1. 이미지 빌드

```bash
docker build -t pet-aegen-teto:latest .
```

### 2. 컨테이너 실행

```bash
docker run -d \
  --name pet-aegen-teto \
  -p 5000:5000 \
  -v $(pwd)/best_model_aegen_teto_ensemble.pth:/app/best_model_aegen_teto_ensemble.pth:ro \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  --restart unless-stopped \
  pet-aegen-teto:latest
```

### 3. 로그 확인

```bash
docker logs -f pet-aegen-teto
```

## 로컬 환경 배포 (Gunicorn)

Docker 없이 직접 배포하는 경우:

### 1. 의존성 설치

```bash
# Python 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 프론트엔드 빌드

```bash
cd frontend
npm install
npm run build
cd ..

# 빌드 결과를 static 폴더로 복사
mkdir -p static
cp -r frontend/dist/* static/
```

### 3. Gunicorn으로 실행

```bash
gunicorn --config gunicorn.conf.py app:app
```

서비스 접속: http://localhost:5000

## 프로덕션 체크리스트

- [ ] 모델 파일 (`best_model_aegen_teto_ensemble.pth`) 존재 확인
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] 필요한 포트 (5000) 개방 확인
- [ ] 환경 변수 설정 (.env 파일 또는 docker-compose.yml)
- [ ] 볼륨 마운트 경로 확인 (uploads, results, 모델 파일)
- [ ] 리소스 제한 설정 (CPU, 메모리)
- [ ] 로그 모니터링 설정
- [ ] 백업 전략 수립 (모델 파일, 업로드 데이터)

## 트러블슈팅

### 모델 로딩 실패

- 모델 파일 경로 확인: `/app/best_model_aegen_teto_ensemble.pth`
- 볼륨 마운트 확인: `docker-compose.yml`의 volumes 섹션
- 로그 확인: `docker-compose logs web | grep "모델"`

### 메모리 부족

- `docker-compose.yml`에서 리소스 제한 조정
- 불필요한 컨테이너 중지

### 포트 충돌

- 5000 포트가 이미 사용 중인 경우
- `docker-compose.yml`에서 포트 변경: `"8080:5000"`

### 정적 파일 404 오류

- 프론트엔드 빌드 확인: `frontend/dist` 폴더 존재 여부
- Dockerfile의 COPY 단계 확인
- 컨테이너 재빌드: `docker-compose up -d --build`

## 성능 최적화

### Worker 수 조정

`gunicorn.conf.py`:
```python
workers = multiprocessing.cpu_count() * 2 + 1
```

### 타임아웃 조정

AI 모델 로딩 시간이 긴 경우:
```python
timeout = 120  # 초 단위
```

### 캐싱

정적 파일 캐싱을 위해 nginx 리버스 프록시 사용 권장

## 모니터링

### 헬스체크

```bash
curl http://localhost:5000/health
```

응답 예시:
```json
{
  "status": "ok",
  "models_loaded": true
}
```

### 리소스 사용량

```bash
docker stats pet-aegen-teto
```

## 업데이트

코드 변경 후 재배포:

```bash
# 컨테이너 중지 및 제거
docker-compose down

# 이미지 재빌드
docker-compose build --no-cache

# 새 컨테이너 시작
docker-compose up -d
```

## 백업

중요 파일 백업:

```bash
# 모델 파일
cp best_model_aegen_teto_ensemble.pth /backup/

# 업로드 데이터
tar -czf uploads_backup.tar.gz uploads/

# 환경 설정
cp .env /backup/
```

## 보안 권장사항

- 프로덕션 환경에서는 HTTPS 사용 (nginx 리버스 프록시 권장)
- `.env` 파일 권한 제한: `chmod 600 .env`
- 불필요한 포트 노출 최소화
- 정기적인 의존성 업데이트
- 로그 모니터링 및 알림 설정
