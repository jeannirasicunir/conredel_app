from rest_framework import serializers
from .models import Alert, RequestLog

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['id', 'type', 'message', 'value', 'threshold', 'state', 'triggered_at', 'resolved_at']
        ordering = ['-triggered_at']

class RequestLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.username if obj.user else None

    class Meta:
        model = RequestLog
        fields = ['id', 'path', 'method', 'status_code', 'duration', 'timestamp', 'user']
        ordering = ['-timestamp']

class MetricSummarySerializer(serializers.Serializer):
    request_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
    active_users = serializers.IntegerField()
    time_window_hours = serializers.IntegerField()

class SlowRequestSerializer(RequestLogSerializer):
    class Meta(RequestLogSerializer.Meta):
        ordering = ['-duration']