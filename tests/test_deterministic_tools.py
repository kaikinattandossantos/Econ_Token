import pytest

from src.deterministic_tools import (
    extract_pure_arithmetic_expression,
    is_pure_arithmetic,
    is_word_problem_with_named_quantities,
    try_deterministic,
)
from src.router import HybridRouter


@pytest.fixture(autouse=True)
def dev_env(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_MOCK", "1")
    monkeypatch.setenv("ALLOWED_MODELS", "mock-remote-model")


def test_percent_of_stays_deterministic():
    prompt = "What is 15% of 340?"
    assert is_pure_arithmetic(prompt)
    result = try_deterministic(prompt)
    assert result is not None
    assert result.text == "51"


def test_two_plus_two_stays_deterministic():
    prompt = "2 + 2"
    assert is_pure_arithmetic(prompt)
    result = try_deterministic(prompt)
    assert result is not None
    assert result.text == "4"


def test_car_word_problem_is_not_deterministic():
    prompt = (
        "A car travels 120 km in 2 hours, then 150 km in 1 hour. "
        "What is the average speed for the whole trip?"
    )
    assert is_word_problem_with_named_quantities(prompt)
    assert not is_pure_arithmetic(prompt)
    assert extract_pure_arithmetic_expression(prompt) is None
    assert try_deterministic(prompt) is None


def test_train_word_problem_routes_to_fireworks(monkeypatch):
    def fake_remote(prompt, model, max_tokens=700, temperature=0.0):
        return {
            "text": "57.1 km/h",
            "tokens_input": 40,
            "tokens_output": 10,
            "tokens_total": 50,
            "tokens_estimated": 50,
            "model": model,
            "cost_credits": 0.0,
            "cost_estimated": 0.0,
        }

    monkeypatch.setattr("src.router.generate_remote", fake_remote)

    prompt = (
        "Math reasoning: A train travels 120 km in 1.5 hours, then slows down and "
        "travels 80 km in 2 hours. What is the average speed for the whole trip in km/h? "
        "Show the calculation."
    )
    assert try_deterministic(prompt) is None

    result = HybridRouter().run(prompt, task_id="math1")
    assert result["route"] == "remote"
    assert "57.1" in result["answer"]