from django.db import models
from django.utils import timezone


class RequestLog(models.Model):
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    duration = models.FloatField()  # in seconds
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['status_code']),
            models.Index(fields=['duration']),
        ]


class Alert(models.Model):
    ALERT_TYPES = [
        ('error_rate', 'High Error Rate'),
        ('slow_response', 'Slow Response Time'),
        ('rate_limit', 'Rate Limit Exceeded'),
    ]
    ALERT_STATES = [
        ('triggered', 'Triggered'),
        ('resolved', 'Resolved'),
    ]

    type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    value = models.FloatField()  # The value that triggered the alert
    threshold = models.FloatField()  # The threshold that was exceeded
    state = models.CharField(max_length=10, choices=ALERT_STATES, default='triggered')
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def resolve(self):
        if self.state == 'triggered':
            self.state = 'resolved'
            self.resolved_at = timezone.now()
            self.save()


class AlertRule(models.Model):
    RULE_TYPES = [
        ('error_rate', 'High Error Rate'),
        ('slow_response', 'Slow Response Time'),
        ('rate_limit', 'Rate Limit Exceeded'),
    ]

    type = models.CharField(max_length=20, choices=RULE_TYPES)
    name = models.CharField(max_length=255)
    threshold = models.FloatField()
    window_minutes = models.IntegerField(default=5)  # Time window to check
    enabled = models.BooleanField(default=True)
    webhook_url = models.URLField(null=True, blank=True)  # Optional webhook for notifications
