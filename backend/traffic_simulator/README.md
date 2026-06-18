# Traffic Simulator Guide

This directory contains traffic simulation scripts that test the backend API's behavior under various load conditions. Use these tools to:

**Test API Resilience**
- Rate limiting effectiveness
- Error handling capabilities
- Performance under load

**Generate Monitoring Data**
- Response time metrics
- Error rate statistics
- Resource utilization patterns

**Validate Configuration**
- Rate limit settings
- Timeout parameters
- Error handling logic

## Available Simulators

1. **Regular Traffic Simulation** 
   ```bash
   python simulate_traffic.py
   ```
   - Simulates normal API usage patterns
   - Sends ~10 requests/second (configurable)
   - Perfect for baseline monitoring
   - Tests all API endpoints evenly

2. **Rate Limit Testing**
   ```bash
   python simulate_traffic_rate_limit.py
   ```
   - Sends 100+ requests/second (configurable)
   - Triggers rate limiting responses
   - Validates rate limit configuration
   - Monitors rate limiting behavior

3. **Slow Request Testing**
   ```bash
   python simulate_traffic_slow.py
   ```
   - Simulates delayed responses
   - Tests timeout handling
   - Logs slow request patterns
   - Validates monitoring alerts

## 📋 Quick Start

### Prerequisites
Python 3.8 or higher
Access to backend API
API authentication token
Python packages: `requests`, `python-dotenv`

### Setup Python Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Environment
Create or edit `/backend/.env`:
```env
# Required Settings
API_TOKEN=your_api_token_here         # Used for authentication
API_BASE_URL=api.example.com          # API endpoint (default: <domain>:8000)

# Optional Settings
REQUESTS_PER_SECOND=10                # Default request rate
SIMULATION_DURATION=3600              # Run time in seconds (0 = infinite)
LOG_LEVEL=INFO                        # Logging detail level

# Django Configuration
DJANGO_DEBUG=True                     # Enable debug mode
DJANGO_SECRET_KEY=your_secret_key     # Django secret key
ALLOWED_HOSTS=localhost,127.0.0.1     # Allowed host list
DATABASE_URL=sqlite:///db.sqlite3     # Database connection
```

**Important Notes**:
- Environment file must be in `/backend/.env`
- All simulators share this configuration
- Default values are used if settings are missing

## Usage Guide

### Regular Traffic Simulation
```bash
python simulate_traffic.py
```
- Sends requests to various endpoints
- Maintains a steady request rate
- Good for general monitoring

### Rate Limit Testing
```bash
python simulate_traffic_rate_limit.py
```
- Sends rapid requests to trigger rate limiting
- Expect to see 429 (Too Many Requests) responses
- Monitor rate limit metrics in Grafana

### Slow Request Testing
```bash
python simulate_traffic_slow.py
```
- Targets endpoints with intentional delays
- Useful for testing slow request detection
- Monitor response times in Grafana

## Monitoring & Analysis

### Grafana Dashboards

#### 1. General Metrics Dashboard
```bash
http://<grafana-url>/d/general_metrics/
```
- Real-time request rates
- Response status distribution
- Response time trends
- Error rate patterns

#### 2. Rate Limiting Analysis
```bash
http://<grafana-url>/d/rate_limit/
```
- Rate limit triggers
- Request frequency heatmap
- Blocked request analysis
- Traffic burst patterns

#### 3. Performance Monitoring
```bash
http://<grafana-url>/d/slow_requests/
```
- Slow request tracking
- Duration percentiles
- Bottleneck identification
- Performance thresholds

### Key Performance Indicators (KPIs)

| Metric | Warning | Critical | Dashboard |
|--------|---------|----------|-----------|
| Request Rate | >100/s | >200/s | General |
| Response Time | >500ms | >1s | Performance |
| Error Rate | >5% | >10% | General |
| Rate Limits | >10/min | >20/min | Rate Limit |
| Slow Requests | >5/min | >10/min | Performance |

## Troubleshooting Guide

### Common Issues & Solutions

#### 1. Authentication Failures
```python
requests.exceptions.HTTPError: 401 Unauthorized
```
**Solutions**:
- Verify API_TOKEN in `.env`
- Check token expiration
- Confirm token permissions

#### 2. Connection Issues
```python
requests.exceptions.ConnectionError
```
**Solutions**:
- Check API is running: `curl http://<domain>:8000/api/health/`
- Verify API_BASE_URL in `.env`
- Test network connectivity

#### 3. Rate Limit Errors
```python
requests.exceptions.HTTPError: 429 Too Many Requests
```
**Expected Behavior**:
- Normal during rate limit testing
- Validates rate limiting works
- Adjust REQUESTS_PER_SECOND if needed

## Pro Tips

### 1. Running Multiple Simulators
```bash
# In separate terminals:
python simulate_traffic.py &        # Background load
python simulate_traffic_slow.py &   # Slow requests
python simulate_traffic_rate_limit.py  # Rate limits
```

### 2. Resource Management
- Monitor CPU/Memory usage
- Use SIMULATION_DURATION to limit runtime
- Clean up with Ctrl+C or `kill` command

### 3. Custom Configurations
```bash
# Set environment variables for quick tests
export REQUESTS_PER_SECOND=50
export SIMULATION_DURATION=300
python simulate_traffic.py
```