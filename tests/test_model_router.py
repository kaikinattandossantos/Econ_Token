import os

import pytest

from src.model_router import select_remote_model
from src.specialist_agents import TaskProfile, analyze_task


@pytest.fixture(autouse=True)
def allowed_models(monkeypatch):
    monkeypatch.setenv(
        "ALLOWED_MODELS",
        "accounts/fireworks/models/minimax-m3,"
        "accounts/fireworks/models/kimi-k2p7-code,"
        "accounts/fireworks/models/gemma-4-31b-it,"
        "accounts/fireworks/models/gemma-4-26b-a4b-it",
    )


def test_code_uses_kimi_when_allowed():
    profile = analyze_task("Debug this traceback in Python: TypeError on line 2")
    decision = select_remote_model(profile)
    assert "kimi" in decision.model


def test_sentiment_uses_low_cost_allowed_model():
    profile = analyze_task("Classify the sentiment: this is great")
    decision = select_remote_model(profile)
    assert "minimax" in decision.model


def test_math_reasoning_prefers_larger_allowed_model():
    profile = analyze_task("Solve this math reasoning problem step by step: if 3x+5=20, x=?")
    decision = select_remote_model(profile)
    assert "31b" in decision.model or "26b" in decision.model


def test_rejects_model_outside_allowed_list(monkeypatch):
    profile = TaskProfile(raw_task="test", normalized_task="test", task_type="sentiment")
    profile.finalize_task_type()

    monkeypatch.setattr(
        "src.model_router._rank_models_for_category",
        lambda category, allowed: ["accounts/fireworks/models/not-allowed"],
    )

    with pytest.raises(SystemExit):
        select_remote_model(profile)