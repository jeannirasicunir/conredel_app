from django.urls import path
from .views import (
    MetricsView, RequestListView, RequestMetricsView,
    SlowRequestListView, AlertHistoryView,
    RateLimitAlertView, SlowRequestMetricsView,
    ErrorMetricsView, RateLimitMetricsView
)

urlpatterns = [
    path("metrics/", MetricsView.as_view(), name="metrics"),
    path("request_log/", RequestListView.as_view(), name="request-log"),
    path("metrics/requests/", RequestMetricsView.as_view(), name="request-metrics"),
    path("alerts/slow-requests/", SlowRequestListView.as_view(), name="alerts-slow-requests"),
    path("metrics/slow-requests/prometheus/", SlowRequestMetricsView.as_view(), name="prometheus-slow-request-metrics"),
    path("alerts/errors/", AlertHistoryView.as_view(), name="alerts-errors"),
    path("alerts/rate/", RateLimitAlertView.as_view(), name="alerts-rate"),
    path("metrics/errors/prometheus/", ErrorMetricsView.as_view(), name="prometheus-error-metrics"),
    path("metrics/rate-limit/prometheus/", RateLimitMetricsView.as_view(), name="prometheus-rate-limit-metrics"),
]