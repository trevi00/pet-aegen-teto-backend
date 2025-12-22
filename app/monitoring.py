"""
애플리케이션 모니터링 모듈
- 요청 수, 응답 시간, 에러 수 추적
- 시스템 리소스 사용량 모니터링
"""

import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import psutil
import os


class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self._lock = threading.Lock()
        self._start_time = datetime.utcnow()

        # 요청 메트릭
        self._request_count = 0
        self._error_count = 0
        self._response_times = []
        self._endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'errors': 0,
            'total_time': 0
        })

        # 최근 1시간 동안의 요청 기록 (분 단위)
        self._hourly_requests = defaultdict(int)

    def record_request(self, endpoint: str, response_time: float, status_code: int):
        """요청 기록"""
        with self._lock:
            self._request_count += 1
            self._response_times.append(response_time)

            # 최근 1000개만 유지
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-1000:]

            # 에러 카운트
            if status_code >= 400:
                self._error_count += 1
                self._endpoint_stats[endpoint]['errors'] += 1

            # 엔드포인트 통계
            self._endpoint_stats[endpoint]['count'] += 1
            self._endpoint_stats[endpoint]['total_time'] += response_time

            # 시간대별 요청 (분 단위)
            current_minute = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            self._hourly_requests[current_minute] += 1

            # 1시간 이상 지난 데이터 정리
            cutoff = (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
            old_keys = [k for k in self._hourly_requests.keys() if k < cutoff]
            for k in old_keys:
                del self._hourly_requests[k]

    def get_metrics(self) -> dict:
        """메트릭 조회"""
        with self._lock:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

            # 평균 응답 시간 계산
            avg_response_time = 0
            if self._response_times:
                avg_response_time = sum(self._response_times) / len(self._response_times)

            # 시스템 리소스
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            # 엔드포인트별 통계
            endpoint_metrics = {}
            for endpoint, stats in self._endpoint_stats.items():
                avg_time = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0
                endpoint_metrics[endpoint] = {
                    'requests': stats['count'],
                    'errors': stats['errors'],
                    'avg_response_time_ms': round(avg_time * 1000, 2)
                }

            return {
                'server': {
                    'uptime_seconds': round(uptime, 2),
                    'uptime_human': str(timedelta(seconds=int(uptime))),
                    'start_time': self._start_time.isoformat() + 'Z'
                },
                'requests': {
                    'total': self._request_count,
                    'errors': self._error_count,
                    'error_rate': round(self._error_count / max(self._request_count, 1) * 100, 2),
                    'avg_response_time_ms': round(avg_response_time * 1000, 2),
                    'requests_per_minute': self._calculate_rpm()
                },
                'endpoints': endpoint_metrics,
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory': {
                        'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                        'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                        'percent': round(process.memory_percent(), 2)
                    },
                    'disk': {
                        'total_gb': round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 2),
                        'used_gb': round(psutil.disk_usage('/').used / 1024 / 1024 / 1024, 2),
                        'percent': psutil.disk_usage('/').percent
                    }
                },
                'hourly_requests': dict(sorted(self._hourly_requests.items())[-60:])
            }

    def _calculate_rpm(self) -> float:
        """분당 요청 수 계산"""
        now = datetime.utcnow()
        one_minute_ago = (now - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M')
        current_minute = now.strftime('%Y-%m-%d %H:%M')

        # 최근 1분간 요청 수
        count = self._hourly_requests.get(current_minute, 0)
        count += self._hourly_requests.get(one_minute_ago, 0)

        return count


# 전역 메트릭 수집기
metrics_collector = MetricsCollector()


def init_monitoring(app):
    """Flask 앱에 모니터링 미들웨어 추가"""

    @app.before_request
    def before_request():
        from flask import request, g
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        from flask import request, g

        # 응답 시간 계산
        response_time = time.time() - getattr(g, 'start_time', time.time())

        # 정적 파일 제외
        if not request.path.startswith('/static'):
            metrics_collector.record_request(
                endpoint=request.path,
                response_time=response_time,
                status_code=response.status_code
            )

        return response

    # /metrics 엔드포인트 등록
    @app.route('/metrics')
    def metrics():
        from flask import jsonify
        return jsonify(metrics_collector.get_metrics())

    # /health 엔드포인트 개선
    @app.route('/health')
    def health():
        from flask import jsonify
        import psutil

        # 시스템 상태 확인
        cpu_ok = psutil.cpu_percent() < 90
        memory_ok = psutil.virtual_memory().percent < 90
        disk_ok = psutil.disk_usage('/').percent < 90

        status = 'healthy' if (cpu_ok and memory_ok and disk_ok) else 'degraded'

        return jsonify({
            'status': status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': {
                'cpu': 'ok' if cpu_ok else 'warning',
                'memory': 'ok' if memory_ok else 'warning',
                'disk': 'ok' if disk_ok else 'warning'
            }
        })

    app.logger.info("Monitoring middleware initialized")
