import json
import os
from datetime import datetime
from .config import LOG_FILE

def log_run(data: dict):
    """Log the run data to a JSONL file."""
    data["timestamp"] = datetime.now().isoformat()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")
