from .task_types import Task, Route, TaskDifficulty
from .deterministic_tools import try_deterministic
from .local_model import generate_local
from .remote_fireworks import generate_remote
from .evaluator import (
    estimate_task_difficulty,
    estimate_local_confidence,
    get_escalation_reason,
    should_escalate,
)
from .config import ROUTING_THRESHOLD, ENABLE_LOCAL_COMPETITION, LOCAL_MODEL_NAME, REMOTE_MODEL_NAME
from .logging_utils import log_run
from .usage import build_usage_summary

class HybridRouter:
    def __init__(self):
        self.threshold = ROUTING_THRESHOLD

    def run(self, task_content: str, task_id: str = "default"):
        task = Task(content=task_content, id=task_id)

        deterministic = try_deterministic(task_content)
        difficulty_score = estimate_task_difficulty(task_content)

        route = Route.LOCAL
        if deterministic:
            route = Route.DETERMINISTIC
        elif difficulty_score >= 0.75:
            route = Route.REMOTE

        final_answer = ""
        local_conf = 0.0
        remote_info = {}
        local_calls = []
        decision_reason = "initial_local_route"

        if route == Route.DETERMINISTIC and deterministic:
            final_answer = deterministic.text
            local_conf = deterministic.confidence
            decision_reason = deterministic.task_type

        if route == Route.LOCAL:
            if ENABLE_LOCAL_COMPETITION:
                ans1 = generate_local(f"Task: {task_content}\nAnswer briefly.")
                ans2 = generate_local(f"Task: {task_content}\nAnswer step by step.")
                local_calls.extend([ans1, ans2])

                final_answer = ans1["text"] if len(ans1["text"]) >= len(ans2["text"]) else ans2["text"]
                route = Route.LOCAL_COMPETITION
            else:
                local_res = generate_local(task_content)
                local_calls.append(local_res)
                final_answer = local_res["text"]

            local_conf = estimate_local_confidence(task_content, final_answer)

            if should_escalate(task, final_answer, local_conf, self.threshold):
                route = Route.REMOTE
                decision_reason = get_escalation_reason(
                    task_content,
                    final_answer,
                    local_conf,
                    self.threshold,
                )
            else:
                decision_reason = "local_answer_accepted"

        if route == Route.REMOTE:
            remote_res = generate_remote(task_content)
            final_answer = remote_res["text"]
            remote_info = remote_res
            if decision_reason == "initial_local_route":
                decision_reason = "high_estimated_difficulty"

        usage = build_usage_summary(local_calls, remote_info, route.value)

        log_data = {
            "task_id": task_id,
            "task": task_content,
            "route": route.value,
            "difficulty_score": difficulty_score,
            "local_confidence": local_conf,
            "local_model": LOCAL_MODEL_NAME,
            "remote_model": remote_info.get("model", REMOTE_MODEL_NAME),
            "remote_tokens": remote_info.get("tokens_total", remote_info.get("tokens_estimated", 0)),
            "decision_reason": decision_reason,
            "usage": usage,
            "answer": final_answer
        }
        log_run(log_data)

        return log_data
