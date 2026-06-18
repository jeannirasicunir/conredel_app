from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter
from rest_framework.renderers import JSONRenderer, BaseRenderer
from django.db import models
import django
import time
from .metrics import MetricsStore
from .models import Alert, RequestLog
from django.utils import timezone
from datetime import timedelta
from .serializers import (
    RequestLogSerializer, AlertSerializer,
    MetricSummarySerializer, SlowRequestSerializer
)

START_TIME = time.time()

from django.http import HttpResponse
import time
from prometheus_client import CollectorRegistry, Gauge, generate_latest

from rest_framework.renderers import JSONRenderer, BaseRenderer

class PrometheusRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'prometheus'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, bytes):
            return data
        return str(data).encode('utf-8')

class HealthView(APIView):
    renderer_classes = [JSONRenderer, PrometheusRenderer]
    registry = CollectorRegistry()
    health_gauge = Gauge('backend_health', 'Backend health status (1 = healthy, 0 = unhealthy)',
                        registry=registry)
    response_time_gauge = Gauge('backend_health_response_time_seconds',
                             'Time taken to generate health check response',
                             registry=registry)

    def get(self, request, *args, **kwargs):
        print("Health check request received")
        format_param = request.query_params.get('format', 'json').lower()
        print(f"Format parameter: {format_param}")
        print(f"Headers: {request.headers}")
        print(f"Path: {request.path}")

        # Start timing the response
        start_time = time.time()
        
        # Determine health status
        try:
            # Add your health checks here
            # For now, we'll just assume it's healthy
            is_healthy = True
            health_status = "ok"
        except Exception:
            is_healthy = False
            health_status = "error"

        # Update metrics
        self.health_gauge.set(1 if is_healthy else 0)
        response_time = time.time() - start_time
        self.response_time_gauge.set(response_time)

        # Generate response based on format
        if format_param == 'prometheus':
            metrics_data = generate_latest(self.registry)
            return Response(metrics_data, content_type='text/plain; version=0.0.4')
        else:
            # JSON response
            response_data = {
                'status': health_status,
                'health': 1 if is_healthy else 0,
                'response_time': response_time,
            }
            return Response(response_data)

class AlertsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Get time range from query parameters or default to last 24 hours
        hours = int(request.query_params.get('hours', 24))
        alert_type = request.query_params.get('type')
        state = request.query_params.get('state')

        since = timezone.now() - timedelta(hours=hours)
        alerts = Alert.objects.filter(triggered_at__gte=since)

        if alert_type:
            alerts = alerts.filter(type=alert_type)
        if state:
            alerts = alerts.filter(state=state)

        alerts = alerts.order_by('-triggered_at')

        return Response({
            'alerts': [{
                'id': alert.id,
                'type': alert.type,
                'message': alert.message,
                'value': alert.value,
                'threshold': alert.threshold,
                'state': alert.state,
                'triggered_at': alert.triggered_at,
                'resolved_at': alert.resolved_at
            } for alert in alerts]
        })

class SlowRequestsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Get slow requests from the last hour
        threshold = float(request.query_params.get('threshold', 1.0))  # Default 1 second
        hours = int(request.query_params.get('hours', 1))
        
        since = timezone.now() - timedelta(hours=hours)
        slow_requests = RequestLog.objects.filter(
            timestamp__gte=since,
            duration__gt=threshold
        ).order_by('-duration')[:100]  # Limit to top 100 slowest

        return Response({
            'threshold': threshold,
            'requests': [{
                'path': req.path,
                'method': req.method,
                'duration': req.duration,
                'status_code': req.status_code,
                'timestamp': req.timestamp,
                'user': req.user.username if req.user else None
            } for req in slow_requests]
        })

from .pagination import MetricsPagination

class BaseMetricsView(ListAPIView):
    pagination_class = MetricsPagination
    filter_backends = [OrderingFilter]

    def get_time_window(self):
        hours = min(max(1, int(self.request.query_params.get('hours', 24))), 168)
        return timezone.now() - timedelta(hours=hours)

class MetricsView(APIView):
    renderer_classes = [JSONRenderer, PrometheusRenderer]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.registry = CollectorRegistry()
        # Initialize metrics
        self.total_requests_gauge = Gauge('total_requests', 'Total number of requests in time window', registry=self.registry)
        self.error_requests_gauge = Gauge('error_requests', 'Number of error requests in time window', registry=self.registry)
        self.avg_response_time_gauge = Gauge('avg_response_time_seconds', 'Average response time in seconds', registry=self.registry)
        self.active_users_gauge = Gauge('active_users', 'Number of active users', registry=self.registry)
    
    def get(self, request):
        hours = min(max(1, int(request.query_params.get('hours', 24))), 168)
        since = timezone.now() - timedelta(hours=hours)
        
        queryset = RequestLog.objects.filter(timestamp__gte=since)
        total_requests = queryset.count()
        error_requests = queryset.filter(status_code__gte=400).count()
        avg_duration = queryset.aggregate(avg_duration=models.Avg('duration'))['avg_duration'] or 0
        active_users = MetricsStore._metrics['active_users']
        
        # Create new registry for each request to avoid stale metrics
        self.registry = CollectorRegistry()
        self.total_requests_gauge = Gauge('total_requests', 'Total number of requests in time window', registry=self.registry)
        self.error_requests_gauge = Gauge('error_requests', 'Number of error requests in time window', registry=self.registry)
        self.avg_response_time_gauge = Gauge('avg_response_time_seconds', 'Average response time in seconds', registry=self.registry)
        self.active_users_gauge = Gauge('active_users', 'Number of active users', registry=self.registry)
        
        # Set current values
        self.total_requests_gauge.set(total_requests)
        self.error_requests_gauge.set(error_requests)
        self.avg_response_time_gauge.set(float(avg_duration))
        self.active_users_gauge.set(active_users)
        
        format_param = request.query_params.get('format', 'json').lower()
        if format_param == 'prometheus':
            metrics_data = generate_latest(self.registry)
            return Response(metrics_data, content_type='text/plain; version=0.0.4')
        
        return Response({
            'request_count': total_requests,
            'error_count': error_requests,
            'avg_response_time': float(avg_duration),
            'active_users': active_users,
            'time_window_hours': hours,
        })

class RequestListView(BaseMetricsView):
    serializer_class = RequestLogSerializer
    ordering_fields = ['timestamp', 'duration', 'status_code', 'method']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        since = self.get_time_window()
        return RequestLog.objects.filter(
            timestamp__gte=since
        ).order_by('-timestamp')


class RequestMetricsView(APIView):
    renderer_classes = [PrometheusRenderer]
    registry = CollectorRegistry()
    
    # Metrics
    request_counter = Gauge('request_counter_total', 'Total number of requests by path and method',
                          ['path', 'method'], registry=registry)
    request_duration_gauge = Gauge('request_duration_seconds', 'Request duration in seconds by path and method',
                                 ['path', 'method'], registry=registry)
    request_duration_histogram = Gauge('request_duration_histogram_seconds', 'Request duration histogram',
                                     ['path', 'method', 'le'], registry=registry)
    request_log = Gauge('request_log', 'Request log with all fields',
                       ['path', 'method', 'status_code', 'duration', 'timestamp', 'user'],
                       registry=registry)
    
    def get(self, request):
        # Get time window from query params or default to 24 hours
        hours = min(max(1, int(request.query_params.get('hours', 24))), 168)
        since = timezone.now() - timedelta(hours=hours)
        
        queryset = RequestLog.objects.filter(
            timestamp__gte=since
        ).order_by('-timestamp')
        
        # Reset metrics (they are gauges, not counters)
        self.request_counter._metrics.clear()
        self.request_duration_gauge._metrics.clear()
        self.request_duration_histogram._metrics.clear()
        self.request_log._metrics.clear()
        
        # Update metrics
        path_method_count = {}
        path_method_durations = {}
        
        for log in queryset:
            path = log.path
            method = log.method
            duration = log.duration
            
            # Count requests by path and method
            key = (path, method)
            if key not in path_method_count:
                path_method_count[key] = 0
            path_method_count[key] += 1
            
            # Collect durations for averaging
            if key not in path_method_durations:
                path_method_durations[key] = []
            path_method_durations[key].append(duration)
            
            # Update histogram buckets
            buckets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float('inf')]
            for bucket in buckets:
                if duration <= bucket:
                    self.request_duration_histogram.labels(
                        path=path,
                        method=method,
                        le=str(bucket)
                    ).inc()
            
            # Update request log
            self.request_log.labels(
                path=path,
                method=method,
                status_code=str(log.status_code),
                duration=str(log.duration),
                timestamp=str(log.timestamp.timestamp()),
                user=log.user.username if log.user else "anonymous"
            ).set(1)
        
        # Update counter and duration metrics
        for (path, method), count in path_method_count.items():
            self.request_counter.labels(path=path, method=method).set(count)
            
            # Calculate average duration
            durations = path_method_durations[(path, method)]
            avg_duration = sum(durations) / len(durations)
            self.request_duration_gauge.labels(path=path, method=method).set(avg_duration)
        
        metrics_data = generate_latest(self.registry)
        return Response(metrics_data, content_type='text/plain; version=0.0.4')

class SlowRequestListView(BaseMetricsView):
    serializer_class = SlowRequestSerializer
    ordering_fields = ['duration', 'timestamp', 'status_code', 'method']
    ordering = ['-duration']
    
    def get_queryset(self):
        since = self.get_time_window()
        return RequestLog.objects.filter(
            timestamp__gte=since,
            duration__gt=MetricsStore.SLOW_RESPONSE_THRESHOLD
        )


from prometheus_client import REGISTRY, Counter, Histogram, Summary

class SlowRequestMetricsView(APIView):
    renderer_classes = [PrometheusRenderer]
    
    # Static metrics that persist between requests
    registry = CollectorRegistry()
    
    # Counter for total slow requests
    slow_requests_total = Counter('slow_requests_total', 'Total number of slow requests',
                                registry=registry)
    
    # Counter for slow requests by path
    slow_requests_by_path = Counter('slow_requests_by_path', 'Number of slow requests by path',
                                  ['path'], registry=registry)
    
    # Summary for request duration by path
    slow_request_duration = Summary('slow_request_duration_seconds',
                                  'Duration of slow requests by path',
                                  ['path'],
                                  registry=registry)
    
    # Histogram for request durations
    duration_histogram = Histogram('slow_request_duration_histogram_seconds',
                                 'Histogram of slow request durations',
                                 ['path'],
                                 buckets=(2.0, 2.5, 3.0, 5.0, 10.0, float('inf')),
                                 registry=registry)
    
    # Counter for detailed request info
    request_details = Counter('slow_request_details_total',
                            'Detailed counter of slow requests',
                            ['path', 'method', 'status_code', 'user'],
                            registry=registry)
    
    def get(self, request):
        print("SlowRequestMetricsView: Received request from", request.META.get('REMOTE_ADDR'))
        hours = min(max(1, int(request.query_params.get('hours', 24))), 168)
        since = timezone.now() - timedelta(hours=hours)
        
        # Get slow requests
        slow_requests = RequestLog.objects.filter(
            timestamp__gte=since,
            duration__gt=MetricsStore.SLOW_RESPONSE_THRESHOLD
        ).order_by('-duration')
        
        # Clear existing samples
        self.registry.collect()
        
        # Reset counters for this time window
        self.slow_requests_total._value.set(0)
        
        print(f"SlowRequestMetricsView: Found {slow_requests.count()} slow requests")
        
        # Set initial total
        self.slow_requests_total.inc(slow_requests.count())
        
        # Process each request
        for req in slow_requests:
            path = req.path
            
            # Increment path counter
            self.slow_requests_by_path.labels(path=path).inc()
            
            # Record duration in summary and histogram
            self.slow_request_duration.labels(path=path).observe(req.duration)
            self.duration_histogram.labels(path=path).observe(req.duration)
            
            # Increment detailed counter
            self.request_details.labels(
                path=path,
                method=req.method,
                status_code=str(req.status_code),
                user=req.user.username if req.user else "anonymous"
            ).inc()
        
        return Response(generate_latest(self.registry), content_type='text/plain; version=0.0.4')

class AlertHistoryView(BaseMetricsView):
    """Shows alerts for error conditions and threshold violations"""
    serializer_class = AlertSerializer
    ordering_fields = ['triggered_at', 'type', 'state']
    ordering = ['-triggered_at']
    
    def get_queryset(self):
        since = self.get_time_window()
        queryset = Alert.objects.filter(triggered_at__gte=since)
        
        # Filter by state if provided
        state = self.request.query_params.get('state')
        if state in ['triggered', 'resolved']:
            queryset = queryset.filter(state=state)
            
        # Filter by type if provided
        alert_type = self.request.query_params.get('type')
        if alert_type:
            queryset = queryset.filter(type=alert_type)
            
        return queryset

class ThresholdAlertListView(BaseMetricsView):
    serializer_class = AlertSerializer
    ordering_fields = ['triggered_at', 'type', 'value', 'threshold']
    ordering = ['-value']  # Order by most exceeded threshold first
    
    def get_queryset(self):
        since = self.get_time_window()
        return Alert.objects.filter(
            triggered_at__gte=since,
            state='triggered',  # Only show currently triggered alerts
            value__gt=models.F('threshold')  # Only show alerts that exceed their threshold
        ).annotate(
            exceed_ratio=models.F('value') / models.F('threshold')
        ).order_by('-exceed_ratio')

class RateLimitAlertView(BaseMetricsView):
    """Shows alerts specifically for rate limit violations"""
    serializer_class = AlertSerializer
    ordering_fields = ['triggered_at', 'path', 'value']
    ordering = ['-triggered_at']
    
    def get_queryset(self):
        since = self.get_time_window()
        queryset = Alert.objects.filter(
            triggered_at__gte=since,
            type='rate_limit'  # Only show rate limit alerts
        )
        
        # Filter by state if provided
        state = self.request.query_params.get('state')
        if state in ['triggered', 'resolved']:
            queryset = queryset.filter(state=state)
            
        # Filter by path if provided
        path = self.request.query_params.get('path')
        if path:
            queryset = queryset.filter(message__icontains=path)
            
        return queryset

class ErrorMetricsView(APIView):
    renderer_classes = [PrometheusRenderer]
    
    def get(self, request):
        hours = min(max(1, int(request.query_params.get('hours', 24))), 168)
        since = timezone.now() - timedelta(hours=hours)
        
        # Create new registry for this request
        registry = CollectorRegistry()
        
        # Create gauge metrics (better for point-in-time values)
        error_total = Gauge('error_requests_total', 'Total number of error requests',
                          registry=registry)
        error_by_path = Gauge('error_requests_by_path', 'Number of error requests by path',
                            ['path'], registry=registry)
        error_by_status = Gauge('error_requests_by_status',
                              'Number of error requests by status code',
                              ['path', 'status'], registry=registry)
        error_by_method = Gauge('error_requests_by_method',
                              'Number of error requests by HTTP method',
                              ['path', 'method'], registry=registry)
        
        # Get error requests and count them
        error_requests = RequestLog.objects.filter(
            timestamp__gte=since,
            status_code__gte=400
        )
        
        # Count errors by different dimensions
        path_counts = {}
        status_counts = {}
        method_counts = {}
        
        for req in error_requests:
            path = req.path
            
            # Count by path
            if path not in path_counts:
                path_counts[path] = 0
            path_counts[path] += 1
            
            # Count by status
            status_key = (path, str(req.status_code))
            if status_key not in status_counts:
                status_counts[status_key] = 0
            status_counts[status_key] += 1
            
            # Count by method
            method_key = (path, req.method)
            if method_key not in method_counts:
                method_counts[method_key] = 0
            method_counts[method_key] += 1
        
        # Set the metrics
        error_total.set(error_requests.count())
        
        for path, count in path_counts.items():
            error_by_path.labels(path=path).set(count)
        
        for (path, status), count in status_counts.items():
            error_by_status.labels(path=path, status=status).set(count)
            
        for (path, method), count in method_counts.items():
            error_by_method.labels(path=path, method=method).set(count)
        
        return Response(generate_latest(registry), content_type='text/plain; version=0.0.4')

class RateLimitMetricsView(APIView):
    renderer_classes = [PrometheusRenderer]
    
    def get(self, request):
        hours = min(max(1, int(request.query_params.get('hours', 24))), 168)
        since = timezone.now() - timedelta(hours=hours)
        
        # Create new registry for this request
        registry = CollectorRegistry()
        
        # Create gauge metrics
        rate_limit_total = Gauge('rate_limit_alerts_total', 'Total number of rate limit alerts',
                               registry=registry)
        rate_by_path = Gauge('rate_limit_alerts_by_path', 'Number of rate limit alerts by path',
                           ['path'], registry=registry)
        rate_by_threshold = Gauge('rate_limit_alerts_by_threshold',
                                'Number of rate limit alerts by threshold value',
                                ['path', 'threshold'], registry=registry)
        rate_by_state = Gauge('rate_limit_alerts_by_state',
                           'Number of rate limit alerts by state',
                           ['path', 'state'], registry=registry)
        
        # Get rate limit alerts
        rate_limit_alerts = Alert.objects.filter(
            triggered_at__gte=since,
            type='rate_limit'
        )
        
        # Count alerts by different dimensions
        path_counts = {}
        threshold_counts = {}
        state_counts = {}
        
        for alert in rate_limit_alerts:
            # Extract path from alert message
            path = alert.message.split(': ')[-1] if ': ' in alert.message else 'unknown'
            threshold = str(alert.threshold)
            state = alert.state
            
            # Count by path
            if path not in path_counts:
                path_counts[path] = 0
            path_counts[path] += 1
            
            # Count by threshold
            threshold_key = (path, threshold)
            if threshold_key not in threshold_counts:
                threshold_counts[threshold_key] = 0
            threshold_counts[threshold_key] += 1
            
            # Count by state
            state_key = (path, state)
            if state_key not in state_counts:
                state_counts[state_key] = 0
            state_counts[state_key] += 1
        
        # Set the metrics
        rate_limit_total.set(rate_limit_alerts.count())
        
        for path, count in path_counts.items():
            rate_by_path.labels(path=path).set(count)
        
        for (path, threshold), count in threshold_counts.items():
            rate_by_threshold.labels(path=path, threshold=threshold).set(count)
            
        for (path, state), count in state_counts.items():
            rate_by_state.labels(path=path, state=state).set(count)
        
        return Response(generate_latest(registry), content_type='text/plain; version=0.0.4')

class StatusView(APIView):
    renderer_classes = [JSONRenderer, PrometheusRenderer]
    registry = CollectorRegistry()
    version_gauge = Gauge('backend_version', 'Backend version', registry=registry)
    django_version_gauge = Gauge('backend_django_version', 'Django version', registry=registry)
    uptime_gauge = Gauge('backend_uptime_seconds', 'Backend uptime in seconds', registry=registry)
    start_time_gauge = Gauge('backend_start_timestamp', 'Backend start time as Unix timestamp', registry=registry)
    current_time_gauge = Gauge('backend_current_timestamp', 'Backend current time as Unix timestamp', registry=registry)

    def get_version_as_number(self, version_str):
        try:
            # Convert version string like "0.1.0" to 0.1
            parts = version_str.split('.')
            return float(f"{parts[0]}.{parts[1]}")
        except (IndexError, ValueError):
            return 0.0

    def get_django_version_as_number(self):
        try:
            version = django.get_version()
            parts = version.split('.')
            return float(f"{parts[0]}.{parts[1]}")
        except (IndexError, ValueError):
            return 0.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set version metrics
        self.version_gauge.set(self.get_version_as_number("0.1.0"))
        self.django_version_gauge.set(self.get_django_version_as_number())

    def get(self, request):
        current_time = time.time()
        uptime = current_time - START_TIME
        
        # Convert timestamps to datetime objects
        from datetime import datetime
        start_datetime = datetime.fromtimestamp(START_TIME).strftime('%Y-%m-%d %H:%M:%S')
        current_datetime = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format uptime nicely
        days, remainder = divmod(uptime, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        formatted_uptime = []
        if days > 0:
            formatted_uptime.append(f"{int(days)}d")
        if hours > 0:
            formatted_uptime.append(f"{int(hours)}h")
        if minutes > 0:
            formatted_uptime.append(f"{int(minutes)}m")
        formatted_uptime.append(f"{seconds:.2f}s")

        # Update metrics
        self.uptime_gauge.set(uptime)
        self.start_time_gauge.set(START_TIME)
        self.current_time_gauge.set(current_time)

        format_param = request.query_params.get('format', 'json').lower()
        if format_param == 'prometheus':
            metrics_data = generate_latest(self.registry)
            return Response(metrics_data, content_type='text/plain; version=0.0.4')
        else:
            return Response({
                "version": "0.1.0",
                "django_version": django.get_version(),
                "uptime": " ".join(formatted_uptime),
                "uptime_seconds": uptime,
                "start_time": start_datetime,
                "current_time": current_datetime
            })


