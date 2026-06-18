import time
import logging
from django.utils.deprecation import MiddlewareMixin
from .metrics import MetricsStore

logger = logging.getLogger(__name__)

# Debug flag to add artificial delay
DEBUG_ADD_DELAY = False  # Set this to False to remove any potential delay

class MetricsMiddleware(MiddlewareMixin):
    def _get_middleware_name(self, middleware):
        if hasattr(middleware, '__name__'):
            return middleware.__name__
        return middleware.__class__.__name__

    def process_request(self, request):
        current_time = time.time()
        print(f"[DEBUG] Starting request to {request.path} at {current_time}")
        request._start_time = current_time
        request._middleware_times = []
        if hasattr(self, 'get_response'):
            request._middleware_times.append(
                (self._get_middleware_name(self), current_time)
            )

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(request, '_middleware_times'):
            request._middleware_times.append(
                ('view_func', time.time())
            )

    def process_response(self, request, response):
        current_time = time.time()
        if hasattr(request, '_middleware_times'):
            request._middleware_times.append(
                ('process_response', current_time)
            )

        # Function to record the timing after the response is sent
        def record_timing(duration, path, status_code, method):
            print(f"[DEBUG] Request completed: {path}. Duration: {duration:.3f}s")
            
            if duration >= 1.0:
                print(f"[DEBUG] Slow request detected! Path: {path}")
                # Print timing breakdown
                if hasattr(request, '_middleware_times'):
                    prev_time = request._start_time
                    print("\nRequest timing breakdown:")
                    for name, curr_time in request._middleware_times:
                        step_duration = curr_time - prev_time
                        print(f"  - {name}: {step_duration:.3f}s")
                        prev_time = curr_time
                
                print("\nMiddleware classes:")
                from django.conf import settings
                for middleware in settings.MIDDLEWARE:
                    print(f"  - {middleware}")

            MetricsStore.record_request(
                path=path,
                duration=duration,
                status_code=status_code,
                method=method,
                user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            )

        # Create a wrapped streaming response that records timing after completion
        def wrapped_response_streaming_content():
            for content in response.streaming_content:
                yield content
            # Record final timing after all content is sent
            duration = time.time() - getattr(request, '_start_time', current_time)
            record_timing(duration, request.path, response.status_code, request.method)

        # If response is streaming, wrap the content generator
        if hasattr(response, 'streaming_content'):
            response.streaming_content = wrapped_response_streaming_content()
        else:
            # For non-streaming responses, record timing now
            duration = current_time - getattr(request, '_start_time', current_time)
            record_timing(duration, request.path, response.status_code, request.method)

        return response
