import httpx
import random
import time
import sys
import signal
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "localhost")
BASE = f"http://{API_BASE_URL}:8000/api/tasks/"
TOKEN = os.getenv("API_TOKEN")
if not TOKEN:
    print("Error: API_TOKEN not found in .env file")
    sys.exit(1)

# Request configurations
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Simulation settings for slow requests
SLOW_REQUEST_DELAY = 2.0  # Add 2 seconds delay to make requests slow
SLOW_THRESHOLD = 1.0  # Requests taking longer than 1 second are considered slow
ERROR_RATE = 0.1  # 10% chance of errors for variety

# ANSI color codes for output
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
RESET = '\033[0m'

# Status options from your Task model
STATUS_CHOICES = ["todo", "in_progress", "done"]

def get_random_task_data():
    """Generate random task data"""
    return {
        "title": f"Task {random.randint(1,1000)}",
        "description": f"Automated task created at {datetime.now()}",
        "status": random.choice(STATUS_CHOICES),
        "priority": random.randint(1,5)
    }

# Create an httpx client with timeout and limits configuration
client = httpx.Client(
    timeout=10.0,  # Increased timeout for slow requests
    limits=httpx.Limits(
        max_keepalive_connections=5,
        max_connections=5,
        keepalive_expiry=5.0
    ),
    http2=False
)

# Cache for task IDs
task_ids = []
TASK_CACHE_TTL = 60  # Refresh cache every 60 seconds
last_cache_refresh = 0

def refresh_task_cache():
    """Refresh the cache of task IDs"""
    global task_ids, last_cache_refresh
    try:
        resp = client.get(BASE, headers=HEADERS)
        if resp.status_code == 200:
            tasks = resp.json().get('results', [])
            if tasks:
                task_ids = [task['id'] for task in tasks]
        last_cache_refresh = time.time()
    except Exception:
        pass

def get_existing_task_id():
    """Get a random task ID from cached tasks"""
    global task_ids, last_cache_refresh
    current_time = time.time()
    
    # Refresh cache if it's expired or empty
    if not task_ids or (current_time - last_cache_refresh) > TASK_CACHE_TTL:
        refresh_task_cache()
    
    return random.choice(task_ids) if task_ids else None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nStopping traffic simulator...")
    client.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print(f"Starting slow request simulator... Press Ctrl+C to stop")
print(f"Using base URL: {BASE}")
print(f"Artificially adding {SLOW_REQUEST_DELAY}s delay to requests")

operations = {
    "GET_LIST": 0,
    "GET_DETAIL": 0,
    "POST": 0,
    "PUT": 0,
    "DELETE": 0
}

try:
    while True:
        try:
            # Determine if this request should have an error
            is_error = random.random() < ERROR_RATE
            
            # Select operation type
            choice = random.choice(["GET_LIST", "GET_DETAIL", "POST", "PUT", "DELETE"])
            
            print(f"\n[DEBUG] Making slow {choice} request")
            start_time = time.time()
            
            if choice == "GET_LIST":
                # Add sleep parameter to make server process slowly
                params = {'sleep': SLOW_REQUEST_DELAY}
                if is_error:
                    params['page'] = 999999  # Invalid page number
                resp = client.get(BASE, headers=HEADERS, params=params)
            
            elif choice == "POST":
                data = get_random_task_data()
                if is_error:
                    data['priority'] = 999  # Invalid priority
                    data['status'] = 'invalid_status'
                resp = client.post(f"{BASE}?sleep={SLOW_REQUEST_DELAY}", json=data, headers=HEADERS)
            
            elif choice in ["GET_DETAIL", "PUT", "DELETE"]:
                task_id = get_existing_task_id()
                if task_id:
                    if is_error:
                        task_id = 99999
                    
                    if choice == "GET_DETAIL":
                        resp = client.get(f"{BASE}{task_id}/?sleep={SLOW_REQUEST_DELAY}", headers=HEADERS)
                    elif choice == "PUT":
                        data = get_random_task_data()
                        if is_error:
                            data['priority'] = 999
                            data['status'] = 'invalid_status'
                        resp = client.put(f"{BASE}{task_id}/?sleep={SLOW_REQUEST_DELAY}", json=data, headers=HEADERS)
                    else:  # DELETE
                        resp = client.delete(f"{BASE}{task_id}/?sleep={SLOW_REQUEST_DELAY}", headers=HEADERS)
                else:
                    print("No existing tasks found, skipping operation")
                    continue
            
            # Calculate total request time
            end_time = time.time()
            request_time = end_time - start_time
            
            # Update statistics and show detailed output
            operations[choice] += 1
            request_type = ["SLOW"]  # All requests are slow
            if is_error:
                request_type.append("ERROR")
                
            # Response time color is always red for slow requests
            time_color = RED

            request_info = f"{', '.join(request_type)}"
            print(f"{datetime.now().strftime('%H:%M:%S')} - {choice}: {resp.status_code} "
                  f"{time_color}({request_time:.3f}s){RESET} [{request_info}]")
            
            # Print statistics every 10 operations
            if sum(operations.values()) % 10 == 0:
                print("\nOperation Statistics:")
                for op, count in operations.items():
                    print(f"{op}: {count}")
                print()
                
        except (httpx.RequestError, httpx.HTTPError) as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        # Random delay between requests (longer to not overwhelm)
        time.sleep(random.uniform(0.5, 2.0))

except KeyboardInterrupt:
    print("\nStopping slow request simulator...")
    client.close()
    print("\nFinal Statistics:")
    for op, count in operations.items():
        print(f"{op}: {count}")