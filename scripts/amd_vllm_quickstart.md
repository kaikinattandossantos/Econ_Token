# AMD GPU Local Model Quickstart

Use this in the AMD notebook image `ROCm + vLLM + PyTorch`.

## 1. Start a small OpenAI-compatible vLLM server

Pick a small instruct model first:

```bash
python -m vllm.entrypoints.openai.api_server \
  --host 0.0.0.0 \
  --port 8001 \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --dtype auto \
  --max-model-len 4096
```

If memory is tight, try:

```bash
python -m vllm.entrypoints.openai.api_server \
  --host 0.0.0.0 \
  --port 8001 \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --dtype auto \
  --max-model-len 4096
```

## 2. Configure the router project

In `.env`:

```ini
LOCAL_PROVIDER=openai_compatible
LOCAL_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
LOCAL_OPENAI_BASE_URL=http://127.0.0.1:8001/v1/chat/completions
LOCAL_OPENAI_API_KEY=local-not-needed
LOCAL_MAX_TOKENS=512
LOCAL_TEMPERATURE=0.0
```

## 3. Smoke test

```bash
python scripts/smoke_local_model.py
```

Expected result:

```text
provider=openai_compatible
model=Qwen/Qwen2.5-1.5B-Instruct
response=ready
```

## Notes

For Track 1, keep Fireworks as the source of final answers if the guide requires the allowed Fireworks models. Use this local model for routing, drafting, verification, and local evaluation.
