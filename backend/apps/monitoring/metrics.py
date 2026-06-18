from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.core.cache import cache
from django.db import models
from datetime import timedelta
import requests
from .models import RequestLog, Alert, AlertRule

class MetricsStore:
    _metrics = {
        "requests": 0,
        "errors": 0,
        "total_duration": 0.0,
        "active_users": 0
    }

    # Alert thresholds
    ERROR_RATE_THRESHOLD = 0.1  # 10% error rate
    SLOW_RESPONSE_THRESHOLD = 1.0  # 1 second
    SLOW_RATE_THRESHOLD = 0.05  # 5% of requests being slow is concerning
    RATE_LIMIT_THRESHOLD = 100  # requests per minute

    @classmethod
    def update_active_users(cls):
        active_time = timezone.now() - timedelta(hours=24)
        # Count users who have made requests in the last 24 hours
        active_users = RequestLog.objects.filter(
            timestamp__gte=active_time,
            user__isnull=False
        ).values_list('user', flat=True).distinct()
        cls._metrics["active_users"] = len(active_users)
        print(f"[DEBUG] Found {len(active_users)} active users in the last 24 hours")
        # Print each active user's request count for debugging
        for user_id in active_users:
            request_count = RequestLog.objects.filter(
                timestamp__gte=active_time,
                user_id=user_id
            ).count()
            print(f"[DEBUG] User {user_id} made {request_count} requests")

    @classmethod
    def check_rate_limit(cls, path):
        """Check if rate limit is exceeded for a path"""
        key = f"rate_limit:{path}"
        current = cache.get(key, 0)
        cache.set(key, current + 1, 60)  # Expire in 60 seconds
        return current > cls.RATE_LIMIT_THRESHOLD

    @classmethod
    def send_alert(cls, alert_type, message, value, threshold, webhook_url=None):
        """Create an alert and optionally send to webhook"""
        alert = Alert.objects.create(
            type=alert_type,
            message=message,
            value=value,
            threshold=threshold
        )
        
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'type': alert_type,
                    'message': message,
                    'value': value,
                    'threshold': threshold,
                    'timestamp': alert.triggered_at.isoformat()
                })
            except Exception as e:
                print(f"Failed to send webhook: {e}")

    @classmethod
    def check_alerts(cls, window_minutes=5):
        """Check for alert conditions"""
        now = timezone.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Get recent requests
        recent_requests = RequestLog.objects.filter(timestamp__gte=window_start)
        total_requests = recent_requests.count()
        
        if total_requests > 0:
            # Check error rate
            error_count = recent_requests.filter(status_code__gte=400).count()
            error_rate = error_count / total_requests
            
            if error_rate > cls.ERROR_RATE_THRESHOLD:
                cls.send_alert(
                    'error_rate',
                    f'High error rate detected: {error_rate:.2%}',
                    error_rate,
                    cls.ERROR_RATE_THRESHOLD
                )
            
            # Check slow responses (duration > threshold)
            slow_requests = recent_requests.filter(
                duration__gt=cls.SLOW_RESPONSE_THRESHOLD
            ).order_by('-duration')
            slow_count = slow_requests.count()
            slow_rate = slow_count / total_requests

            if slow_rate > cls.SLOW_RATE_THRESHOLD:
                # Get the slowest requests for the alert message
                slowest_requests = slow_requests[:5]
                slow_details = "\n".join([
                    f"  - {req.path}: {req.duration:.2f}s ({req.method})"
                    for req in slowest_requests
                ])
                
                cls.send_alert(
                    'slow_response',
                    f'High number of slow responses detected ({slow_count} of {total_requests} requests)\n'
                    f'Slow request rate: {slow_rate:.2%}\n'
                    f'Average response time: {recent_requests.aggregate(avg=models.Avg("duration"))["avg"]:.2f}s\n'
                    f'Slowest requests:\n{slow_details}',
                    slow_rate,
                    cls.SLOW_RATE_THRESHOLD
                )
                
            # Individual slow request alerts for very slow responses (2x threshold)
            very_slow_requests = recent_requests.filter(
                duration__gt=cls.SLOW_RESPONSE_THRESHOLD * 2
            ).exclude(path__contains='/metrics/')  # Exclude metrics endpoint
            
            for req in very_slow_requests:
                cls.send_alert(
                    'very_slow_response',
                    f'Very slow response detected!\n'
                    f'Path: {req.path}\n'
                    f'Method: {req.method}\n'
                    f'Duration: {req.duration:.2f}s\n'
                    f'Status: {req.status_code}',
                    req.duration,
                    cls.SLOW_RESPONSE_THRESHOLD * 2
                )

    @classmethod
    def record_request(cls, path, duration, status_code, method='GET', user=None):
        # Update metrics
        cls._metrics["requests"] += 1
        cls._metrics["total_duration"] += duration
        if status_code >= 400:
            cls._metrics["errors"] += 1

        # Log request
        RequestLog.objects.create(
            path=path,
            method=method,
            status_code=status_code,
            duration=duration,
            user=user
        )
        
        # Update active users count after each request
        if user and user.is_authenticated:
            print(f"[DEBUG] Recording authenticated request from user {user.id}")
            cls.update_active_users()

        # Individual slow request alert
        if duration > cls.SLOW_RESPONSE_THRESHOLD and '/metrics/' not in path:
            cls.send_alert(
                'slow_request',
                f'Slow request detected!\n'
                f'Path: {path}\n'
                f'Method: {method}\n'
                f'Duration: {duration:.2f}s\n'
                f'Status: {status_code}',
                duration,
                cls.SLOW_RESPONSE_THRESHOLD
            )

        # Check rate limiting
        if cls.check_rate_limit(path):
            cls.send_alert(
                'rate_limit',
                f'Rate limit exceeded for path: {path}',
                cls.RATE_LIMIT_THRESHOLD + 1,
                cls.RATE_LIMIT_THRESHOLD
            )

        # Check for alerts
        cls.check_alerts()

    @classmethod
    def get_error_metrics(cls):
        """Get prometheus-formatted error metrics"""
        recent_errors = RequestLog.objects.filter(status_code__gte=400)

        # Error metrics by endpoint
        error_by_path = {}
        for log in recent_errors:
            if log.path not in error_by_path:
                error_by_path[log.path] = {
                    'total': 0,
                    'by_status': {},
                    'by_method': {}
                }
            error_by_path[log.path]['total'] += 1
            error_by_path[log.path]['by_status'][log.status_code] = error_by_path[log.path]['by_status'].get(log.status_code, 0) + 1
            error_by_path[log.path]['by_method'][log.method] = error_by_path[log.path]['by_method'].get(log.method, 0) + 1

        metrics = []
        
        # Total errors
        metrics.append(f'# HELP error_requests_total Total number of error requests\n')
        metrics.append(f'# TYPE error_requests_total counter\n')
        metrics.append(f'error_requests_total {recent_errors.count()}\n')
        
        # Errors by path
        metrics.append(f'# HELP error_requests_by_path Error requests grouped by path\n')
        metrics.append(f'# TYPE error_requests_by_path counter\n')
        for path, data in error_by_path.items():
            metrics.append(f'error_requests_by_path{{path="{path}"}} {data["total"]}\n')
            
        # Errors by status code
        metrics.append(f'# HELP error_requests_by_status Error requests grouped by status code\n')
        metrics.append(f'# TYPE error_requests_by_status counter\n')
        for path, data in error_by_path.items():
            for status, count in data['by_status'].items():
                metrics.append(f'error_requests_by_status{{path="{path}",status="{status}"}} {count}\n')

        # Errors by method
        metrics.append(f'# HELP error_requests_by_method Error requests grouped by HTTP method\n')
        metrics.append(f'# TYPE error_requests_by_method counter\n')
        for path, data in error_by_path.items():
            for method, count in data['by_method'].items():
                metrics.append(f'error_requests_by_method{{path="{path}",method="{method}"}} {count}\n')

        return ''.join(metrics)

    @classmethod
    def get_metrics(cls, page=1, page_size=10, hours=24):
        avg = cls._metrics["total_duration"] / cls._metrics["requests"] if cls._metrics["requests"] else 0
        cls.update_active_users()

        since = timezone.now() - timedelta(hours=hours)

        # Get paginated recent alerts
        alerts_start = (page - 1) * page_size
        alerts_end = alerts_start + page_size
        total_alerts = Alert.objects.filter(triggered_at__gte=since).count()
        recent_alerts = Alert.objects.filter(
            triggered_at__gte=since
        ).order_by('-triggered_at')[alerts_start:alerts_end]

        # Get recent requests
        total_requests = RequestLog.objects.filter(timestamp__gte=since).count()
        recent_requests = RequestLog.objects.filter(
            timestamp__gte=since
        ).order_by('-timestamp')[alerts_start:alerts_end]

        # Get slow requests
        slow_requests = RequestLog.objects.filter(
            timestamp__gte=since,
            duration__gt=cls.SLOW_RESPONSE_THRESHOLD
        ).order_by('-duration')[alerts_start:alerts_end]
        total_slow_requests = RequestLog.objects.filter(
            timestamp__gte=since,
            duration__gt=cls.SLOW_RESPONSE_THRESHOLD
        ).count()

        return {
            "summary": {
                "request_count": cls._metrics["requests"],
                "error_count": cls._metrics["errors"],
                "avg_response_time": avg,
                "active_users": cls._metrics["active_users"],
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_alerts": total_alerts,
                "total_requests": total_requests,
                "total_slow_requests": total_slow_requests,
                "total_pages": max(
                    (total_alerts + page_size - 1) // page_size,
                    (total_requests + page_size - 1) // page_size,
                    (total_slow_requests + page_size - 1) // page_size
                )
            },
            "recent_requests": [{
                "path": req.path,
                "method": req.method,
                "status_code": req.status_code,
                "duration": req.duration,
                "timestamp": req.timestamp,
                "user": req.user.username if req.user else None
            } for req in recent_requests],
            "recent_alerts": [{
                "type": alert.type,
                "message": alert.message,
                "triggered_at": alert.triggered_at,
                "state": alert.state,
                "value": alert.value,
                "threshold": alert.threshold
            } for alert in recent_alerts],
            "slow_requests": [{
                "path": req.path,
                "method": req.method,
                "status_code": req.status_code,
                "duration": req.duration,
                "timestamp": req.timestamp,
                "user": req.user.username if req.user else None
            } for req in slow_requests]
        }
