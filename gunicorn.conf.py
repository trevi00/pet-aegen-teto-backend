"""
Gunicorn 프로덕션 설정
고성능 WSGI 서버 설정 파일
"""

import os

# 서버 소켓
bind = "0.0.0.0:5000"
backlog = 2048

# Worker 프로세스
workers = int(os.environ.get('GUNICORN_WORKERS', '1'))
worker_class = "sync"
worker_connections = 1000
timeout = 120  # AI 모델 로딩을 위해 타임아웃 증가
keepalive = 5

# 스레드
threads = 2

# 서버 메커니즘
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# 로깅
errorlog = "-"  # stderr
loglevel = "info"
accesslog = "-"  # stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 프로세스 네이밍
proc_name = "pet-aegen-teto"

# 서버 후크
def on_starting(server):
    """
    서버 시작 시 호출
    """
    print("=" * 60)
    print("Starting Gunicorn server...")
    print(f"Workers: {workers}")
    print(f"Bind: {bind}")
    print("=" * 60)

def when_ready(server):
    """
    서버 준비 완료 시 호출
    """
    print("Server is ready. Spawning workers")

def on_reload(server):
    """
    Worker 재시작 시 호출
    """
    print("Worker reloading...")
