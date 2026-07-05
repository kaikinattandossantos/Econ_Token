from .task_types import Task, Route, TaskDifficulty
from .local_model import generate_local
from .remote_fireworks import generate_remote
from .evaluator import estimate_task_difficulty, estimate_local_confidence, should_escalate
from .config import ROUTING_THRESHOLD, ENABLE_LOCAL_COMPETITION, LOCAL_MODEL_NAME, REMOTE_MODEL_NAME
from .logging_utils import log_run

class HybridRouter:
    def __init__(self):
        self.threshold = ROUTING_THRESHOLD

    def run(self, task_content: str, task_id: str = "default"):
        task = Task(content=task_content, id=task_id)
        
        # 1. Estimate difficulty
        difficulty_score = estimate_task_difficulty(task_content)
        
        route = Route.LOCAL
        if difficulty_score > 0.8:
            route = Route.REMOTE
            
        final_answer = ""
        local_conf = 0.0
        remote_info = {}
        
        if route == Route.LOCAL:
            # Try local first
            if ENABLE_LOCAL_COMPETITION:
                # Simple version of local competition
                ans1 = generate_local(f"Task: {task_content}\nAnswer briefly.")
                ans2 = generate_local(f"Task: {task_content}\nAnswer step by step.")
                
                # Heuristic: use the longer one if they differ significantly
                final_answer = ans1 if len(ans1) >= len(ans2) else ans2
                route = Route.LOCAL_COMPETITION
            else:
                final_answer = generate_local(task_content)
            
            local_conf = estimate_local_confidence(task_content, final_answer)
            
            # Check if escalation is needed
            if should_escalate(task, final_answer, local_conf, self.threshold):
                route = Route.REMOTE
        
        if route == Route.REMOTE:
            remote_res = generate_remote(task_content)
            final_answer = remote_res["text"]
            remote_info = remote_res
            
        # Logging
        log_data = {
            "task_id": task_id,
            "task": task_content,
            "route": route.value,
            "difficulty_score": difficulty_score,
            "local_confidence": local_conf,
            "local_model": LOCAL_MODEL_NAME,
            "remote_model": remote_info.get("model", REMOTE_MODEL_NAME),
            "remote_tokens": remote_info.get("tokens_estimated", 0),
            "answer": final_answer
        }
        log_run(log_data)
        
        return log_data
