from django.urls import path
from . import views

urlpatterns = [
    path('prometheus/', views.ErrorMetricsView.as_view(), name='error-metrics'),
]