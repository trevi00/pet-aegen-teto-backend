# AWS 배포 가이드

반려동물 에겐 vs 테토 분류 시스템을 AWS에 배포하는 가이드입니다.

## 배포 옵션 비교

| 방법 | 난이도 | 비용 | 관리 | 추천도 |
|------|--------|------|------|--------|
| **EC2 + Docker** | 중 | 저~중 | 직접 관리 | ⭐⭐⭐⭐⭐ |
| **App Runner** | 낮음 | 중 | AWS 관리 | ⭐⭐⭐⭐ |
| **ECS Fargate** | 중~높음 | 중~높음 | AWS 관리 | ⭐⭐⭐ |

**추천: EC2 + Docker Compose** (가장 간단하고 비용 효율적)

---

## 방법 1: EC2 + Docker Compose (추천)

### 장점
- 기존 docker-compose.yml을 그대로 사용
- 직접 제어 가능
- 비용 효율적
- 디버깅 용이

### 단계별 가이드

#### 1. EC2 인스턴스 생성

**1.1 AWS Console 접속**
- [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
- 리전 선택 (서울: ap-northeast-2)

**1.2 인스턴스 시작**
```
Launch Instance 클릭

인스턴스 설정:
- Name: pet-aegen-teto-server
- AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
- Instance type: t3.medium (2 vCPU, 4GB RAM) 이상
  * AI 모델 로딩을 위해 최소 4GB RAM 필요
  * t3.medium (약 $0.0416/시간, ~$30/월)
  * 또는 t3.large (4 vCPU, 8GB RAM) 권장 (~$60/월)

- Key pair: 새로 생성하거나 기존 것 선택 (중요! 다운로드 보관)

- Network settings:
  * Create security group
  * SSH (22): My IP (또는 Anywhere - 보안 주의)
  * Custom TCP (5000): Anywhere (0.0.0.0/0, ::/0)
  * HTTPS (443): Anywhere (선택사항)

- Storage: 30GB gp3 (AI 모델 저장 공간)
```

**1.3 Elastic IP 할당 (선택사항, 추천)**
```
Elastic IPs → Allocate Elastic IP address
할당된 IP를 EC2 인스턴스에 Associate
```

#### 2. 서버 초기 설정

**2.1 SSH 접속**
```bash
# Windows (PowerShell)
ssh -i "your-key.pem" ubuntu@<EC2-Public-IP>

# 권한 오류 시 (Windows)
# 파일 우클릭 → 속성 → 보안 → 고급 → 상속 사용 안함 → 본인만 남기고 제거
```

**2.2 시스템 업데이트 및 Docker 설치**
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
sudo apt install -y docker.io docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 사용자를 docker 그룹에 추가 (sudo 없이 docker 실행)
sudo usermod -aG docker ubuntu

# 재로그인 (그룹 권한 적용)
exit
# 다시 SSH 접속
ssh -i "your-key.pem" ubuntu@<EC2-Public-IP>

# 설치 확인
docker --version
docker-compose --version
```

#### 3. 프로젝트 배포

**3.1 코드 업로드 방법**

**방법 A: Git 사용 (추천)**
```bash
# Git 설치
sudo apt install -y git

# 프로젝트 클론
git clone https://github.com/your-username/pet-aegen-teto-test.git
cd pet-aegen-teto-test
```

**방법 B: 파일 직접 전송 (SCP)**
```bash
# 로컬에서 실행 (Windows PowerShell)
# 프로젝트 압축
tar -czf project.tar.gz C:\Users\user\pet-aegen-teto-test

# EC2로 전송
scp -i "your-key.pem" project.tar.gz ubuntu@<EC2-Public-IP>:~/

# EC2에서 압축 해제
ssh -i "your-key.pem" ubuntu@<EC2-Public-IP>
tar -xzf project.tar.gz
cd pet-aegen-teto-test
```

**3.2 모델 파일 업로드**
```bash
# 로컬에서 실행 (모델 파일 전송)
scp -i "your-key.pem" C:\Users\user\pet-aegen-teto-test\best_model_aegen_teto_ensemble.pth ubuntu@<EC2-Public-IP>:~/pet-aegen-teto-test/
```

**3.3 환경 변수 설정**
```bash
# EC2에서 실행
cd pet-aegen-teto-test
cp .env.example .env

# .env 파일 편집 (필요시)
nano .env
```

**3.4 Docker Compose로 실행**
```bash
# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 상태 확인
docker-compose ps
```

#### 4. 접속 확인

```bash
# 헬스체크
curl http://<EC2-Public-IP>:5000/health

# 브라우저에서 접속
http://<EC2-Public-IP>:5000
```

#### 5. 도메인 연결 (선택사항)

**5.1 Route 53 사용**
```
1. Route 53 → Hosted zones → Create hosted zone
2. 도메인 등록 (또는 기존 도메인 연결)
3. Create record
   - Record name: www (또는 비워두기)
   - Record type: A
   - Value: <EC2-Elastic-IP>
   - TTL: 300
4. Create record

접속: http://your-domain.com:5000
```

**5.2 HTTPS 설정 (nginx + Let's Encrypt)**
```bash
# nginx 설치
sudo apt install -y nginx certbot python3-certbot-nginx

# nginx 설정
sudo nano /etc/nginx/sites-available/pet-aegen-teto

# 다음 내용 입력:
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 설정 활성화
sudo ln -s /etc/nginx/sites-available/pet-aegen-teto /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL 인증서 발급 (Let's Encrypt)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 설정 확인
sudo systemctl status certbot.timer

# 접속
https://your-domain.com
```

#### 6. 모니터링 및 관리

**로그 확인**
```bash
# 실시간 로그
docker-compose logs -f

# 최근 100줄
docker-compose logs --tail=100

# 특정 서비스
docker-compose logs web
```

**재시작**
```bash
# 애플리케이션 재시작
docker-compose restart

# 전체 재빌드
docker-compose down
docker-compose up -d --build
```

**서버 재부팅 시 자동 시작**
```bash
# systemd 서비스 생성
sudo nano /etc/systemd/system/pet-aegen-teto.service

# 다음 내용 입력:
[Unit]
Description=Pet Aegen Teto Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/pet-aegen-teto-test
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

# 서비스 활성화
sudo systemctl enable pet-aegen-teto.service
sudo systemctl start pet-aegen-teto.service
```

#### 7. 비용 최적화

**인스턴스 중지/시작 자동화**
```bash
# CloudWatch Events + Lambda로 야간/주말 중지 가능
# 또는 AWS Instance Scheduler 사용
```

**예약 인스턴스**
```
장기 사용 시 Reserved Instance 구매 (최대 72% 할인)
1년 약정: ~40% 할인
3년 약정: ~60% 할인
```

---

## 방법 2: AWS App Runner

### 장점
- 가장 간단한 배포
- 자동 스케일링
- HTTPS 자동 설정
- 관리 부담 없음

### 단점
- 비용이 더 높음 (~$50-100/월)
- 대용량 모델 파일 처리 제약

### 배포 단계

#### 1. ECR에 이미지 푸시

```bash
# AWS CLI 설치 및 구성
aws configure

# ECR 레포지토리 생성
aws ecr create-repository --repository-name pet-aegen-teto --region ap-northeast-2

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 빌드
docker build -t pet-aegen-teto .

# 태그 지정
docker tag pet-aegen-teto:latest <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/pet-aegen-teto:latest

# 푸시
docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/pet-aegen-teto:latest
```

#### 2. App Runner 서비스 생성

```
AWS Console → App Runner → Create service

Source:
- Source: Container registry
- Provider: Amazon ECR
- Container image URI: <ECR-image-URI>

Deployment settings:
- Automatic deployment 체크

Configure service:
- Service name: pet-aegen-teto
- Port: 5000
- CPU: 2 vCPU
- Memory: 4 GB

Environment variables:
- FLASK_ENV=production
- PYTHONUNBUFFERED=1

Create & Deploy
```

#### 3. 접속

```
App Runner가 제공하는 URL로 접속
https://xxxxx.ap-northeast-2.awsapprunner.com
```

---

## 방법 3: ECS Fargate

### 장점
- 서버리스 컨테이너
- 오토스케일링
- AWS 네이티브 통합

### 단점
- 설정 복잡
- 비용 높음

### 간단 가이드

```bash
# ECS CLI 설치
# Task Definition 작성
# ECS 클러스터 생성
# Service 배포
```

자세한 ECS 가이드는 별도 요청 시 제공하겠습니다.

---

## 보안 권장사항

### 1. Security Group 설정
```
최소 권한 원칙:
- SSH (22): My IP만 허용
- HTTP (80/5000): 필요한 경우에만 Anywhere
- HTTPS (443): Anywhere
- 나머지: 모두 차단
```

### 2. IAM 역할
```
EC2 인스턴스에 최소 권한 IAM Role 할당
- CloudWatch Logs 전송
- S3 접근 (모델 파일 저장 시)
```

### 3. 데이터 백업
```bash
# S3에 모델 및 데이터 백업
aws s3 sync ./uploads s3://your-bucket/backups/uploads/
aws s3 sync ./results s3://your-bucket/backups/results/
```

### 4. 모니터링
```
CloudWatch:
- EC2 메트릭 모니터링
- 로그 수집
- 알람 설정 (CPU > 80%, Memory > 90%)
```

---

## 예상 비용 (월별)

### EC2 방식
```
EC2 t3.medium: ~$30
EBS 30GB: ~$3
Data Transfer: ~$5
Total: ~$40/월
```

### App Runner
```
vCPU (2): ~$25
Memory (4GB): ~$25
Requests: ~$10
Total: ~$60-100/월
```

### 비용 절감 팁
```
1. Reserved Instance (1년): 40% 절감
2. Spot Instance: 최대 90% 절감 (중단 위험 있음)
3. 야간/주말 인스턴스 중지: 40-60% 절감
4. CloudFront CDN: 정적 파일 캐싱으로 트래픽 비용 절감
```

---

## 트러블슈팅

### 1. 포트 접속 안됨
```bash
# Security Group 확인
# 인바운드 규칙에 포트 5000 추가되었는지 확인

# 방화벽 확인
sudo ufw status
sudo ufw allow 5000
```

### 2. Docker 메모리 부족
```bash
# 인스턴스 타입 업그레이드
# t3.medium → t3.large (4GB → 8GB)
```

### 3. 모델 로딩 실패
```bash
# 모델 파일 경로 확인
ls -lh best_model_aegen_teto_ensemble.pth

# 로그 확인
docker-compose logs | grep "모델"
```

---

## 다음 단계

1. ✅ EC2 인스턴스 생성
2. ✅ Docker 설치 및 프로젝트 배포
3. ⬜ 도메인 연결
4. ⬜ HTTPS 설정
5. ⬜ 모니터링 설정
6. ⬜ 백업 자동화
7. ⬜ CI/CD 파이프라인 구축 (GitHub Actions)

---

## GitHub Actions CI/CD (선택사항)

`.github/workflows/deploy.yml` 파일 생성:

```yaml
name: Deploy to EC2

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Deploy to EC2
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.EC2_HOST }}
        username: ubuntu
        key: ${{ secrets.EC2_SSH_KEY }}
        script: |
          cd ~/pet-aegen-teto-test
          git pull origin main
          docker-compose down
          docker-compose up -d --build
```

GitHub Repository → Settings → Secrets → Actions:
- `EC2_HOST`: EC2 Public IP
- `EC2_SSH_KEY`: Private key 내용

---

## 지원

문제 발생 시:
1. 로그 확인: `docker-compose logs -f`
2. 헬스체크: `curl http://localhost:5000/health`
3. 시스템 리소스: `docker stats`
