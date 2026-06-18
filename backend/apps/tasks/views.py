import time
import hashlib
from functools import wraps
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from .models import Task
from .serializers import TaskSerializer

def time_it(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        print(f"[DEBUG] {f.__name__} took {end - start:.3f} seconds")
        return result
    return wrapper

class TaskViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "priority"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at"]

    def _get_cache_key(self):
        """Generate a cache key based on user and query params"""
        cache_parts = [
            f"tasks_user_{self.request.user.id}",
            str(self.request.GET.urlencode())
        ]
        key = "_".join(cache_parts)
        return hashlib.md5(key.encode()).hexdigest()

    @time_it
    def get_queryset(self):
        # Check for sleep parameter to simulate slow processing
        sleep_time = self.request.GET.get('sleep')
        if sleep_time:
            try:
                sleep_seconds = float(sleep_time)
                print(f"[DEBUG] Artificially sleeping for {sleep_seconds} seconds")
                time.sleep(sleep_seconds)
            except ValueError:
                pass

        cache_key = self._get_cache_key()
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            print("[DEBUG] Cache hit for tasks list")
            return cached_data

        print("[DEBUG] Cache miss for tasks list")
        # Only tasks owned by the user
        queryset = Task.objects.select_related('owner').filter(owner=self.request.user)
        cache.set(cache_key, queryset, timeout=60)  # Cache for 60 seconds
        return queryset

    @time_it
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        # Invalidate cache for this user's tasks
        cache_pattern = f"tasks_user_{self.request.user.id}*"
        cache.delete_pattern(cache_pattern) if hasattr(cache, 'delete_pattern') else cache.clear()

    @time_it
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @time_it
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @time_it
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @time_it
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @time_it
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
