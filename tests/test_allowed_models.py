import pytest

from src.allowed_models import ensure_model_allowed, get_allowed_models, normalize_task_type


def test_normalize_task_type_maps_legacy_labels():
    assert normalize_task_type("sequence") == "math_reasoning"
    assert normalize_task_type("logic_puzzle") == "logical_reasoning"
    assert normalize_task_type("unknown_label") == "factual_qa"


def test_get_allowed_models_requires_env(monkeypatch):
    monkeypatch.delenv("ALLOWED_MODELS", raising=False)
    monkeypatch.delenv("ALLOW_DEV_MOCK", raising=False)
    with pytest.raises(SystemExit):
        get_allowed_models()


def test_ensure_model_allowed_rejects_unknown(monkeypatch):
    monkeypatch.setenv("ALLOWED_MODELS", "model-a,model-b")
    with pytest.raises(SystemExit):
        ensure_model_allowed("model-c")