import subprocess
import json
import time

def get_logs():
    cmd = [
        "gcloud", "logging", "read",
        'resource.type="cloud_run_revision" AND resource.labels.service_name="gemma-assistant" AND timestamp >= "2026-05-15T05:15:00Z"',
        "--project=logical-contact-496003-p1",
        "--format=json",
        "--limit=50",
        "--order=desc"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs = json.loads(result.stdout)
        for log in logs:
            timestamp = log.get("timestamp")
            payload = log.get("textPayload", log.get("jsonPayload", "No payload"))
            print(f"[{timestamp}] {payload}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_logs()
