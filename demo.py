import httpx
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"

def log_step(title):
    print(f"\n{'='*50}")
    print(f"STEP: {title}")
    print(f"{'='*50}")

def run_demo():
    # 1. Create a task
    log_step("Creating a new task")
    task_data = {
        "title": "Complete AI-400 Project",
        "description": "Build Task Management API with Agent Skills",
        "priority": 3,
        "due_date": (datetime.utcnow() + timedelta(hours=5)).isoformat()
    }
    with httpx.Client() as client:
        r = client.post(f"{BASE_URL}/tasks/", json=task_data)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
        task_id = r.json()["id"]

        # 2. Add an old completed task
        log_step("Adding an old completed task for cleanup demo")
        old_task_data = {
            "title": "Ancient Task",
            "status": "completed",
            "priority": 1
        }
        r = client.post(f"{BASE_URL}/tasks/", json=old_task_data)
        
        # 3. Show all tasks
        log_step("Retrieving all tasks")
        r = client.get(f"{BASE_URL}/tasks/")
        print(json.dumps(r.json(), indent=2))

        # 4. Run Priority Skill
        log_step("Running 'Auto-Prioritize' Skill")
        print("This skill boosts priority for tasks due within 24 hours.")
        r = client.post(f"{BASE_URL}/skills/prioritize")
        print(r.json()["message"])

        # 5. Get Daily Brief
        log_step("Running 'Daily Brief' Skill")
        r = client.get(f"{BASE_URL}/skills/brief")
        print(f"Brief response: {r.json()['brief']}")

        # 6. Run Cleanup Skill
        log_step("Running 'Database Cleanup' Skill")
        print("Removing completed tasks (simulating archiving)...")
        # For demo purposes, we'll manually update the updated_at to be old if we could, 
        # but here we'll just run it. In a real scenario, it checks the date.
        r = client.post(f"{BASE_URL}/skills/cleanup?days=0") # 0 days to catch our 'Ancient Task'
        print(r.json()["message"])

        # 7. Generate Report
        log_step("Generating Markdown Report")
        r = client.get(f"{BASE_URL}/skills/report")
        print(r.json()["report"])

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Make sure the FastAPI server is running on http://127.0.0.1:8000")
