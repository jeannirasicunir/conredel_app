"""
URL configuration for taskmgr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.users.views import CustomAuthToken
from apps.monitoring.views import HealthView
from .views import welcome_view


urlpatterns = [
    path("", welcome_view, name="api-root"),
    path("admin/", admin.site.urls),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/auth-token/", CustomAuthToken.as_view(), name="api_token_auth"),
    path("api/users/", include("apps.users.urls")),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/status/", include("apps.monitoring.urls_status")),
    path("api/", include("apps.monitoring.urls_metrics")),
    path("api-auth/", include("rest_framework.urls")),  # This adds the login/logout views
]
