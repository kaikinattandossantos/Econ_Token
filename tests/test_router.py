import pytest
from src.router import HybridRouter
from src.evaluator import estimate_task_difficulty, should_escalate
from src.task_types import Task

def test_difficulty_estimation():
    easy_task = "What is 2+2?"
    hard_task = "Prove the Riemann hypothesis step by step with code examples."
    
    assert estimate_task_difficulty(easy_task) < estimate_task_difficulty(hard_task)

def test_should_escalate():
    task = Task(content="Test task")
    # Low confidence should escalate
    assert should_escalate(task, "Short answer", 0.2, 0.7) == True
    # High confidence should not escalate
    assert should_escalate(task, "Long and detailed answer", 0.9, 0.7) == False

def test_router_mock_remote():
    router = HybridRouter()
    # Force a hard task to trigger remote
    res = router.run("Complex medical diagnosis for a rare condition involving legal implications.")
    assert "remote" in res["route"]
    assert "[MOCK REMOTE]" in res["answer"]
