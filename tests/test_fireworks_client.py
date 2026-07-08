import pytest

from src.fireworks_client import (
    FireworksCompletionError,
    _chat_completions_url,
    _extract_choice_text,
    _extract_completion_text,
    generate_completion,
)


def test_chat_url_accepts_full_endpoint():
    assert (
        _chat_completions_url("https://api.fireworks.ai/inference/v1/chat/completions")
        == "https://api.fireworks.ai/inference/v1/chat/completions"
    )


def test_chat_url_accepts_harness_base_url():
    assert (
        _chat_completions_url("https://proxy.example/v1")
        == "https://proxy.example/v1/chat/completions"
    )


def test_extract_choice_text_from_string_content():
    choice = {"message": {"content": "positive"}}
    assert _extract_choice_text(choice) == "positive"


def test_extract_choice_text_from_missing_content_returns_empty():
    choice = {"message": {"role": "assistant"}}
    assert _extract_choice_text(choice) == ""


def test_extract_choice_text_from_list_content_parts():
    choice = {
        "message": {
            "content": [
                {"type": "text", "text": "mixed"},
            ]
        }
    }
    assert _extract_choice_text(choice) == "mixed"


def test_extract_completion_text_raises_when_content_missing():
    with pytest.raises(FireworksCompletionError):
        _extract_completion_text({"choices": [{"message": {"role": "assistant"}}]})


def test_generate_completion_retries_fallback_model(monkeypatch):
    monkeypatch.setenv("ALLOWED_MODELS", "model-a,model-b")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")
    monkeypatch.setenv("FIREWORKS_BASE_URL", "https://api.example/v1/chat/completions")

    calls = []

    def fake_post(**kwargs):
        calls.append(kwargs["model"])
        if kwargs["model"] == "model-a":
            raise FireworksCompletionError("empty completion")
        return {
            "text": "recovered",
            "tokens_input": 12,
            "tokens_output": 4,
            "tokens_total": 16,
            "tokens_estimated": 16,
            "model": kwargs["model"],
            "cost_credits": 0.0,
            "cost_estimated": 0.0,
        }

    monkeypatch.setattr("src.fireworks_client._post_chat_completion", fake_post)

    result = generate_completion("Classify sentiment", model="model-a")
    assert result["text"] == "recovered"
    assert result["model"] == "model-b"
    assert calls == ["model-a", "model-a", "model-b"]