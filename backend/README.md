# Django Backend Documentation

## Overview

This Django application provides a robust task management system with comprehensive monitoring capabilities.

### Core Features
**Task Management**
- CRUD operations for tasks
- Priority levels (1-5)
- Status tracking (todo, in-progress, done)
- Detailed task history

**Security & Performance**
- Token-based authentication
- Rate limiting protection
- Request monitoring
- Performance metrics

**Monitoring Suite**
- Health checks
- System metrics
- Request tracking
- Error monitoring
- Alert management

## Quick Start

```bash
# 1. Set up environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Initialize database
python manage.py migrate
python manage.py createsuperuser

# 5. Run development server
python manage.py runserver

# 6. Get your API token
curl -X POST http://<domain>:8000/api-auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

## API Documentation

### Authentication
All API endpoints (except the monitoring apis) require token authentication.
```http
Authorization: Token your-api-token-here
```

### Tasks API (`/api/tasks/`)

#### List Tasks
```http
GET /api/tasks/
```
- **Description**: Retrieve a paginated list of tasks
- **Query Parameters**:
  - `page`: Page number (default: 1)
  - `page_size`: Items per page (default: 10)
  - `status`: Filter by status (`todo`, `in_progress`, `done`)
  - `priority`: Filter by priority (1-5)
- **Response**: 
  ```json
  {
    "count": 100,
    "next": "http:/url:8000/api/tasks/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "title": "Sample Task",
        "description": "Task description",
        "status": "todo",
        "priority": 3,
        "created_at": "2025-10-27T10:00:00Z",
        "updated_at": "2025-10-27T10:00:00Z"
      }
    ]
  }
  ```

#### Create Task
```http
POST /api/tasks/
```
- **Description**: Create a new task
- **Request Body**:
  ```json
  {
    "title": "New Task",
    "description": "Task description",
    "status": "todo",
    "priority": 3
  }
  ```
- **Fields**:
  - `title`: Required, string, max 200 chars
  - `description`: Optional, text
  - `status`: Required, one of: `todo`, `in_progress`, `done`
  - `priority`: Required, integer 1-5 (1: lowest, 5: highest)

#### Get Task Details
```http
GET /api/tasks/{id}/
```
- **Description**: Retrieve details of a specific task
- **Parameters**:
  - `id`: Task ID (integer)
- **Response**: Full task object

#### Update Task
```http
PUT /api/tasks/{id}/
```
- **Description**: Update all fields of a specific task
- **Parameters**:
  - `id`: Task ID (integer)
- **Request Body**: Same as CREATE
- **Response**: Updated task object

#### Patch Task
```http
PATCH /api/tasks/{id}/
```
- **Description**: Partially update a task
- **Parameters**:
  - `id`: Task ID (integer)
- **Request Body**: Any subset of task fields
- **Response**: Updated task object

#### Delete Task
```http
DELETE /api/tasks/{id}/
```
- **Description**: Delete a specific task
- **Parameters**:
  - `id`: Task ID (integer)
- **Response**: 204 No Content

#### Login
```http
POST /api-auth/login/
```
- **Description**: Login
- **Fields**:
  - `username`: Required, string, max 200 chars
  - `passwrod`: Required, string, max 200 chars

#### Logout
```http
POST /api-auth/logout/
```
- **Description**: Logout

### Monitoring API

#### Health & Status
| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/health/` | GET | Basic health check | No |
| `/api/status/` | GET | Detailed system status | Yes |

Example Health Check:
```bash
curl http://<domain>:8000/api/health/

{
  "status": "ok",
  "health": 1,
  "response_time": 0.000005722045898437
}
```

Example System Status:
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://<domain>:8000/api/status/

{
  "version": "1.0.0",
  "django_version": "4.2.6",
  "uptime": "2d 3h 45m",
  "start_time": "2025-10-25T10:00:00Z",
  "current_time": "2025-10-27T13:45:00Z",
  "database_status": "healthy",
  "cache_status": "connected"
}

#### Request Log
```http
GET /api/request_log/
```
- **Description**: Get a detailed log of the requests made
- **Response**: Details including:
  - ID
  - Path
  - Method
  - Status code
  - Duration
  - Timestamp
  - User

#### Request Metrics
```http
GET /api/metrics/
```
- **Description**: Get request-related metrics
- **Response**: Includes:
  - Request counts
  - Error count
  - Average response time
  - Active users

#### Slow requests
```http
GET /api/alerts/slow-requests/
```
- **Description**: Get the alerts log on the slow requests
- **Response**: Includes:
  - ID
  - Path
  - Method
  - Status code
  - Duration
  - Timestamp
  - User

#### Error history
```http
GET /api/alerts/errors/
```
- **Description**: Get the alerts log on the error requests
- **Response**: Includes:
  - ID
  - Type
  - Message
  - Value
  - Threshold
  - State
  - Triggered at

## Rate Limiting

```http
GET /api/alerts/rate/
```
- **Description**: Get the alerts log on the rate limit requests
- **Response**: Includes:
  - ID
  - Type
  - Message
  - Value
  - Threshold
  - State
  - Triggered at

The API implements rate limiting to prevent abuse:

- **Anonymous Users**: 
  - 100 requests per hour
  - 5 requests per minute

- **Authenticated Users**:
  - 1000 requests per hour
  - 100 requests per minute

Rate limit headers in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1635321600
```

## Monitoring Features

### Request Tracking
- Response time monitoring
- Request duration histograms
- Status code counting
- Error rate tracking

### Performance Metrics
- Cache hit/miss rates
- Rate limit

### Error Tracking
- Error aggregation
- Stack trace collection
- Error frequency analysis
- Error categorization

## Development Guide

### Environment Configuration

Create a `.env` file in the backend directory:

```env
#-----------------------------------------------
# Django Core Settings
#-----------------------------------------------
DJANGO_SECRET_KEY=your-secret-key        # Required: Django secret key
DJANGO_DEBUG=False                       # Optional: Debug mode (default: False)
ALLOWED_HOSTS=localhost,127.0.0.1        # Required: Comma-separated hosts

#-----------------------------------------------
# API Configuration
#-----------------------------------------------
API_TOKEN=your-api-token                 # Required: API authentication token
API_BASE_URL=your-api-domain            # Optional: API domain (default: localhost)

#-----------------------------------------------
# Rate Limiting
#-----------------------------------------------
RATE_LIMIT_PER_MINUTE=100               # Optional: Per-minute limit (default: 100)
RATE_LIMIT_PER_HOUR=1000                # Optional: Per-hour limit (default: 1000)

#-----------------------------------------------
# Monitoring Configuration
#-----------------------------------------------
GF_SECURITY_ADMIN_USER=admin             # Optional: Grafana admin user
GF_SECURITY_ADMIN_PASSWORD=admin         # Optional: Grafana admin password
SLOW_REQUEST_THRESHOLD=2.0               # Optional: Slow request threshold in seconds
ERROR_ALERT_THRESHOLD=10                 # Optional: Error count threshold
```

### Project Structure

```
backend/
├── apps/                      # Application modules
│   ├── monitoring/            # Monitoring functionality
│   │   ├── metrics.py        # Metric collectors
│   │   ├── middleware.py     # Request tracking
│   │   └── views.py         # Monitoring endpoints
│   ├── tasks/                # Task management
│   │   ├── models.py        # Task data models
│   │   ├── serializers.py   # API serializers
│   │   └── views.py         # Task endpoints
│   └── users/                # User management
│       ├── models.py        # User models
│       └── views.py         # Auth endpoints
├── taskmgr/                  # Core configuration
│   ├── settings.py          # Django settings
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI configuration
└── traffic_simulator/        # Load testing tools
```

### Development Tools

```bash
# Code Formatting
black .                  # Format code
isort .                 # Sort imports

# Linting
flake8                  # Check code style
mypy .                  # Type checking

# Testing
python manage.py test              # Run all tests
pytest apps/tasks/tests.py         # Run specific tests
coverage run manage.py test        # Run with coverage
coverage report                    # View coverage report
```

### Testing Guide

```bash
# 1. Run all tests
python manage.py test

# 2. Run specific app tests
python manage.py test apps.tasks.tests

# 3. Run with verbosity
python manage.py test -v 2

# 4. Run with coverage
coverage run manage.py test
coverage report --show-missing
```

### Code Style Guidelines

- Follow PEP 8 standards
- Use type hints for function parameters
- Write docstrings for classes and functions
- Keep functions focused and small
- Use meaningful variable names

Example:
```python
from typing import List, Optional

def get_active_tasks(user_id: int, status: Optional[str] = None) -> List[Task]:
    """Retrieve active tasks for a specific user.

    Args:
        user_id: The ID of the user
        status: Optional status filter

    Returns:
        List of Task objects matching the criteria
    """
    tasks = Task.objects.filter(user_id=user_id)
    if status:
        tasks = tasks.filter(status=status)
    return tasks.filter(is_active=True)
```
