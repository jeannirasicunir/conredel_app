import requests
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
INVALID_HEADERS = {"Authorization": "Token invalid_token"}

# Configure requests session for better performance
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,  # Number of connection pools to cache
    pool_maxsize=10,     # Number of connections to save in the pool
    max_retries=0,       # Disable retries
    pool_block=False     # Don't block when pool is full
)
session.mount('http://', adapter)

# Configure low-level socket options
import socket
socket.setdefaulttimeout(5)  # 5 second timeout

# Simulation settings
ERROR_RATE = 0.2  # 20% chance of simulating errors
INVALID_AUTH_RATE = 0.1  # 10% chance of invalid authentication

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

# Cache for task IDs
task_ids = []
TASK_CACHE_TTL = 60  # Refresh cache every 60 seconds
last_cache_refresh = 0

def refresh_task_cache():
    """Refresh the cache of task IDs"""
    global task_ids, last_cache_refresh
    try:
        resp = requests.get(BASE, headers=HEADERS)
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
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print(f"Starting traffic simulator... Press Ctrl+C to stop")
print(f"Using base URL: {BASE}")

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
            # Determine the type of request simulation
            is_error = random.random() < ERROR_RATE
            is_invalid_auth = random.random() < INVALID_AUTH_RATE
            
            # Select operation type
            choice = random.choice(["GET_LIST", "GET_DETAIL", "POST", "PUT", "DELETE"])
            
            # Prepare request parameters
            current_headers = INVALID_HEADERS if is_invalid_auth else HEADERS
            
            # Add detailed request timing
            session = requests.Session()
            session.headers.update(current_headers)

            # Create a hook to capture timing information
            def timing_hook(resp, *args, **kwargs):
                resp.connection_time = kwargs.get('connection_time', 0)
                resp.dns_time = kwargs.get('dns_time', 0)
                resp.request_time = kwargs.get('request_time', 0)
                resp.ssl_time = kwargs.get('ssl_time', 0)

            # Use the global session instead of creating a new one
            session.headers.update(current_headers)

            if choice == "GET_LIST":
                # Simulate pagination and filter errors
                params = {}
                if is_error:
                    params = {'page': 999999}  # Invalid page number
                print(f"\n[DEBUG] Making GET request to {BASE}")
                print("[DEBUG] DNS lookup starting...")
                start_dns = time.time()
                try:
                    import socket
                    socket.gethostbyname('localhost')
                except:
                    pass
                dns_time = time.time() - start_dns
                print(f"[DEBUG] DNS lookup took: {dns_time:.3f}s")
                
                print("[DEBUG] Starting connection...")
                start_conn = time.time()
                resp = session.get(BASE, params=params, hooks={'response': timing_hook})
            
            elif choice == "POST":
                data = get_random_task_data()
                if is_error:
                    # Generate invalid data
                    data['priority'] = 999  # Invalid priority
                    data['status'] = 'invalid_status'
                print("[DEBUG] Starting connection...")
                start_conn = time.time()
                resp = requests.post(
                    BASE,
                    json=data,
                    headers=current_headers
                )
            
            elif choice in ["GET_DETAIL", "PUT", "DELETE"]:
                task_id = get_existing_task_id()
                if task_id:
                    # For error cases, use invalid task ID
                    if is_error:
                        task_id = 99999
                    
                    if choice == "GET_DETAIL":
                        print("[DEBUG] Starting connection...")
                        start_conn = time.time()
                        resp = requests.get(f"{BASE}{task_id}/", headers=current_headers)
                    elif choice == "PUT":
                        data = get_random_task_data()
                        if is_error:
                            data['priority'] = 999
                            data['status'] = 'invalid_status'
                        print("[DEBUG] Starting connection...")
                        start_conn = time.time()
                        resp = requests.put(
                            f"{BASE}{task_id}/",
                            json=data,
                            headers=current_headers
                        )
                    else:  # DELETE
                        print("[DEBUG] Starting connection...")
                        start_conn = time.time()
                        resp = requests.delete(f"{BASE}{task_id}/", headers=current_headers)
                else:
                    print("No existing tasks found, skipping operation")
                    continue
            
            # Update statistics and show detailed output
            operations[choice] += 1
            request_type = []
            if is_error:
                request_type.append("ERROR")
            if is_invalid_auth:
                request_type.append("INVALID_AUTH")
            if not request_type:
                request_type.append("NORMAL")
                
            # Determine response time color and info
            response_time = resp.elapsed.total_seconds()
            if response_time > 1.0:  # More than 1 second
                time_color = RED
            elif response_time > 0.7:  # More than 700ms
                time_color = YELLOW
            else:
                time_color = GREEN

            request_info = f"{', '.join(request_type)}"
            print(f"{datetime.now().strftime('%H:%M:%S')} - {choice}: {resp.status_code} "
                  f"{time_color}({response_time:.3f}s){RESET} [{request_info}]")
            
            # Print request timing details
            conn_time = time.time() - start_conn
            print(f"[DEBUG] Connection time: {conn_time:.3f}s")
            print(f"[DEBUG] Total request time from library: {resp.elapsed.total_seconds():.3f}s")
            
            # Print low-level socket info
            if hasattr(resp, 'raw') and hasattr(resp.raw, '_connection') and hasattr(resp.raw._connection, 'sock'):
                sock = resp.raw._connection.sock
                if sock:
                    print(f"[DEBUG] Socket timeout: {sock.gettimeout()}")
                    print(f"[DEBUG] Socket family: {sock.family}")
                    print(f"[DEBUG] Socket type: {sock.type}")

            # Print statistics every 50 operations
            if sum(operations.values()) % 50 == 0:
                print("\nOperation Statistics:")
                for op, count in operations.items():
                    print(f"{op}: {count}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if hasattr(e, 'response'):
                print(f"[DEBUG] Response headers: {e.response.headers}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        # Random delay between requests (minimal delay)
        time.sleep(random.uniform(0.01, 0.1))

except KeyboardInterrupt:
    print("\nStopping traffic simulator...")
    print("\nFinal Statistics:")
    for op, count in operations.items():
        print(f"{op}: {count}")
