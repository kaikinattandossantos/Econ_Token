from src.router import HybridRouter
from src.evaluator import estimate_local_confidence, estimate_task_difficulty, should_escalate
from src.task_types import Task
from src.deterministic_tools import try_deterministic

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

def test_simple_translation_is_deterministic():
    res = try_deterministic('traduz para o ingles "bom dia"')
    assert res is not None
    assert res.text == "Good morning."

def test_boa_viagem_sand_estimate_is_deterministic():
    router = HybridRouter()
    res = router.run("calcule quantos graos de areia provavelmente tem na praia de BV de recife")
    assert res["route"] == "deterministic"
    assert "10^17" in res["answer"]

def test_bad_local_translation_confidence_is_low():
    answer = '"Bom Dia" significa Aloca e pode ser usado em muitas atividades diarias.'
    confidence = estimate_local_confidence('traduz para o ingles "bom dia"', answer)
    assert confidence < 0.7

def test_milky_way_stars_is_deterministic():
    router = HybridRouter()
    res = router.run("calcule quantas estrelas temos na via lactea")
    assert res["route"] == "deterministic"
    assert "100 bilhoes" in res["answer"]

def test_short_milky_way_followup_is_deterministic():
    res = try_deterministic("da galaxia via lactea")
    assert res is not None
    assert "estrelas" in res.text

def test_bad_milky_way_answer_confidence_is_low():
    answer = "A Terra: 840.000. Oceano Pacifico: 5,700.000. India: 2,000.000."
    confidence = estimate_local_confidence("calcule quantas estrelas temos na via lactea", answer)
    assert confidence < 0.7
