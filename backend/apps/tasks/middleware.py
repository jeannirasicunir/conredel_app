import time
from django.utils.deprecation import MiddlewareMixin

class SlowRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Add artificial delay if sleep parameter is present"""
        sleep_time = request.GET.get('sleep')
        if sleep_time:
            try:
                sleep_seconds = float(sleep_time)
                print(f"[DEBUG] Adding artificial delay of {sleep_seconds}s")
                time.sleep(sleep_seconds)
            except ValueError:
                pass  # Invalid sleep parameter, ignore