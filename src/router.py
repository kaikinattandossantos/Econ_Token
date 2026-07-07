"""Track 1 submission router.

Pipeline (Rules 4 + 8):
  1. try_deterministic  -> zero scored tokens when genuinely computable
  2. Fireworks remote   -> all LLM final answers (English only)

generate_local is never used for final answers written to results.json.
"""

from __future__ import annotations

from .evaluator import estimate_task_difficulty
from .logging_utils import log_run
from .model_router import select_remote_model
from .remote_fireworks import generate_remote
from .specialist_agents import analyze_task, build_remote_prompt
from .task_types import Route, Task
from .template_responder import try_template_response
from .usage import build_usage_summary


class HybridRouter:
    def run(self, task_content: str, task_id: str = "default"):
        task = Task(content=task_content, id=task_id)

        profile = analyze_task(task_content)
        deterministic = try_template_response(profile)
        difficulty_score = max(estimate_task_difficulty(task_content), profile.score)

        route = Route.REMOTE
        final_answer = ""
        local_conf = 0.0
        remote_info: dict = {}
        local_calls: list = []
        decision_reason = "fireworks_remote_default"

        if deterministic:
            route = Route.DETERMINISTIC
            final_answer = deterministic.text
            local_conf = deterministic.confidence
            decision_reason = f"deterministic_{deterministic.task_type}"
        else:
            remote_prompt = build_remote_prompt(task_content, profile)
            model_decision = select_remote_model(profile)
            remote_res = generate_remote(
                remote_prompt,
                model=model_decision.model,
                max_tokens=model_decision.max_tokens,
                temperature=model_decision.temperature,
            )
            final_answer = remote_res["text"]
            remote_info = remote_res
            remote_info["model_reason"] = model_decision.reason
            decision_reason = f"fireworks_{profile.task_type}"

        usage = build_usage_summary(local_calls, remote_info, route.value)

        log_data = {
            "task_id": task_id,
            "task": task_content,
            "route": route.value,
            "difficulty_score": difficulty_score,
            "local_confidence": local_conf,
            "local_model": None,
            "remote_model": remote_info.get("model", ""),
            "remote_model_reason": remote_info.get("model_reason", ""),
            "remote_tokens": remote_info.get("tokens_total", remote_info.get("tokens_estimated", 0)),
            "decision_reason": decision_reason,
            "specialists": {
                "task_type": profile.task_type,
                "domain": profile.domain,
                "route_hint": profile.route_hint,
                "risk": profile.risk,
                "complexity": profile.complexity,
                "expected_answer": profile.expected_answer,
                "constraints": profile.constraints,
                "signals": profile.signals,
                "semantic": profile.semantic,
            },
            "usage": usage,
            "answer": final_answer,
        }
        log_run(log_data)
        return log_data