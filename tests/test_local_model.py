import pytest

from src.local_model import generate_local


@pytest.fixture(autouse=True)
def allow_local_dev(monkeypatch):
    monkeypatch.setenv("ALLOW_LOCAL_DEV", "1")


def test_local_mock_provider(monkeypatch):
    monkeypatch.setattr("src.local_model.LOCAL_PROVIDER", "mock")
    result = generate_local("hello")
    assert result["provider"] == "mock"
    assert result["cost_credits"] == 0.0
    assert result["dev_only"] is True
    assert "[MOCK LOCAL]" in result["text"]


def test_local_openai_provider_error_is_structured(monkeypatch):
    monkeypatch.setattr("src.local_model.LOCAL_PROVIDER", "openai_compatible")
    monkeypatch.setattr("src.local_model.LOCAL_OPENAI_BASE_URL", "http://127.0.0.1:1/v1/chat/completions")
    result = generate_local("hello")
    assert result["provider"] == "openai_compatible"
    assert result["text"].startswith("Error calling local model:")


def test_local_blocked_without_dev_flag(monkeypatch):
    monkeypatch.delenv("ALLOW_LOCAL_DEV", raising=False)
    with pytest.raises(RuntimeError, match="dev-only"):
        generate_local("hello")