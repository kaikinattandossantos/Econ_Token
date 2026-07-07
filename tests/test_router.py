import os

import pytest

from src.deterministic_tools import try_deterministic
from src.evaluator import estimate_local_confidence, estimate_task_difficulty, should_escalate
from src.router import HybridRouter
from src.task_types import Task


@pytest.fixture(autouse=True)
def dev_env(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_MOCK", "1")
    monkeypatch.setenv("ALLOWED_MODELS", "mock-remote-model")


def test_difficulty_estimation():
    easy_task = "What is 2+2?"
    hard_task = "Prove the Riemann hypothesis step by step with code examples."
    assert estimate_task_difficulty(easy_task) < estimate_task_difficulty(hard_task)


def test_should_escalate():
    task = Task(content="Test task")
    assert should_escalate(task, "Short answer", 0.2, 0.7) is True
    assert should_escalate(task, "Long and detailed answer", 0.9, 0.7) is False


def test_router_uses_fireworks_for_non_deterministic(monkeypatch):
    def fake_remote(prompt, model, max_tokens=700, temperature=0.0):
        return {
            "text": "[MOCK REMOTE] ok",
            "tokens_input": 1,
            "tokens_output": 1,
            "tokens_total": 2,
            "tokens_estimated": 2,
            "model": model,
            "cost_credits": 0.0,
            "cost_estimated": 0.0,
        }

    monkeypatch.setattr("src.router.generate_remote", fake_remote)
    router = HybridRouter()
    res = router.run("Complex medical diagnosis for a rare condition involving legal implications.")
    assert res["route"] == "remote"
    assert "[MOCK REMOTE]" in res["answer"]


def test_counting_sequence_is_deterministic():
    router = HybridRouter()
    res = router.run("count from 0 to 10")
    assert res["route"] == "deterministic"
    assert res["answer"] == "0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10"


def test_long_counting_sequence_is_deterministic():
    router = HybridRouter()
    res = router.run("count from 0 to 100")
    assert res["route"] == "deterministic"
    assert res["answer"].startswith("0, 1, 2")
    assert res["answer"].endswith("98, 99, 100")


def test_arithmetic_is_deterministic():
    router = HybridRouter()
    res = router.run("What is 17 * 3?")
    assert res["route"] == "deterministic"
    assert res["answer"] == "51"


def test_removed_canned_fact_templates():
    assert try_deterministic("calculate how many stars are in the Milky Way") is None
    assert try_deterministic("estimate grains of sand on Boa Viagem beach") is None
    assert try_deterministic("create an arm workout plan for the gym") is None


def test_bad_remote_answer_confidence_is_low():
    answer = "The Earth: 840,000. Pacific Ocean: 5,700,000."
    confidence = estimate_local_confidence("how many stars are in the Milky Way", answer)
    assert confidence < 0.7