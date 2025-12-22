# ========================================
# Stage 1: 프론트엔드 빌드
# ========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 의존성 파일 복사 및 설치
COPY frontend/package*.json ./
RUN npm ci

# 소스 코드 복사 및 빌드
COPY frontend/ ./
RUN npm run build

# ========================================
# Stage 2: 백엔드 런타임
# ========================================
FROM python:3.11-slim

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 프론트엔드 빌드 결과를 static 폴더로 복사
RUN mkdir -p static
COPY --from=frontend-builder /app/frontend/dist ./static

# 업로드 및 결과 폴더 생성
RUN mkdir -p uploads results

# 모델 파일 확인 (존재하지 않으면 경고)
RUN if [ ! -f "best_model_aegen_teto_ensemble.pth" ]; then \
        echo "WARNING: best_model_aegen_teto_ensemble.pth not found!"; \
    fi

# 포트 노출
EXPOSE 5000

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Gunicorn으로 실행
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
