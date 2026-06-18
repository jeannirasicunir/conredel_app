from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def welcome_view(request):
    available_endpoints = {
        "welcome_message": "Welcome to the Task Manager API!",
        "available_endpoints": {
            "API Root": "/",
            "Admin Interface": "/admin/",
            "Authentication": {
                "Get Auth Token": "/api/auth-token/",
                "Login/Logout": {
                    "Login": "/api-auth/login/",
                    "Logout": "/api-auth/logout/",
                }
            },
            "Tasks": {
                "List and Create": "/api/tasks/",
                "Detail, Update, Delete": "/api/tasks/{task_id}/",
            },
            "Users": {
                "List and Create": "/api/users/",
                "Detail, Update, Delete": "/api/users/{user_id}/",
            },
            "Monitoring": {
                "Health Check": "/api/health/",
                "System Status": "/api/status/",
                "Request Log": "/api/request_log/",
                "Metrics": "/api/metrics/",
                "Alerts": {
                    "Slow Requests": "/api/alerts/slow-requests/",
                    "High Error Rates": "/api/alerts/errors/",
                    "Rate limiting Violations": "/api/alerts/rate/",
                }
            },
        },
        "documentation": {
            "message": "Each endpoint supports standard HTTP methods (GET, POST, PUT, DELETE) as appropriate.",
            "authentication": "Most endpoints require authentication. Use the endpoints mentioned above to obtain a token or login/logout.",
            "pagination": "Endpoints are paginated with 5 items per page.",
            "filters": "Endpoints support filtering by different parameters.",
        }
    }
    return Response(available_endpoints)