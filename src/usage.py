from typing import Dict, Any, List


def _pct(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 1)


def build_usage_summary(
    local_calls: List[Dict[str, Any]],
    remote_info: Dict[str, Any],
    route: str,
) -> Dict[str, Any]:
    local_input = sum(call.get("tokens_input", 0) for call in local_calls)
    local_output = sum(call.get("tokens_output", 0) for call in local_calls)
    local_total = sum(call.get("tokens_total", 0) for call in local_calls)

    remote_input = remote_info.get("tokens_input", 0)
    remote_output = remote_info.get("tokens_output", 0)
    remote_total = remote_info.get("tokens_total", 0)
    remote_credits = remote_info.get("cost_credits", 0.0)

    total_tokens = local_total + remote_total
    total_credits = remote_credits

    token_breakdown = [
        {
            "label": "Modelo Local",
            "tokens": local_total,
            "input_tokens": local_input,
            "output_tokens": local_output,
            "percentage": _pct(local_total, total_tokens),
            "credits": 0.0,
            "credit_percentage": 0.0 if total_credits == 0 else 0.0,
        },
        {
            "label": "Modelo Remoto",
            "tokens": remote_total,
            "input_tokens": remote_input,
            "output_tokens": remote_output,
            "percentage": _pct(remote_total, total_tokens),
            "credits": remote_credits,
            "credit_percentage": 100.0 if total_credits > 0 else 0.0,
        },
    ]

    if total_credits > 0:
        token_breakdown[0]["credit_percentage"] = 0.0
        token_breakdown[1]["credit_percentage"] = 100.0

    savings_tokens = local_total if remote_total > 0 else 0
    always_remote_estimate = total_tokens if remote_total == 0 else total_tokens

    return {
        "route": route,
        "tokens": {
            "local_input": local_input,
            "local_output": local_output,
            "local_total": local_total,
            "remote_input": remote_input,
            "remote_output": remote_output,
            "remote_total": remote_total,
            "total": total_tokens,
        },
        "credits": {
            "total_spent": round(total_credits, 6),
            "remote_only": round(remote_credits, 6),
            "saved_vs_always_remote": round(
                (local_total / max(always_remote_estimate, 1)) * remote_credits, 6
            ) if remote_credits > 0 else round(local_total * 0.0000005, 6),
            "breakdown": token_breakdown,
        },
        "local_calls": len(local_calls),
    }