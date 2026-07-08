# Track 1 Docker Submission

This image is designed for the AMD Developer Hackathon ACT II Track 1 harness.

## Runtime Contract

The container reads:

```text
/input/tasks.json
```

and writes:

```text
/output/results.json
```

The entrypoint is:

```dockerfile
ENTRYPOINT ["python", "-m", "src.submission"]
```

Required runtime environment variables are injected by the harness:

```text
FIREWORKS_API_KEY
FIREWORKS_BASE_URL
ALLOWED_MODELS
```

No `.env` file is used in the submitted image because `DISABLE_DOTENV=1` is set.

## Hugging Face Cache

The Dockerfile downloads these sentence-transformers models during build:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
sentence-transformers/all-MiniLM-L6-v2
```

Runtime is offline for embeddings:

```text
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
```

This avoids startup downloads from `huggingface.co`.

## Build And Push

Docker Hub:

```bash
docker buildx build \
  --platform linux/amd64 \
  --tag YOUR_DOCKERHUB_USER/router-agent-track1:latest \
  --push .
```

GHCR:

```bash
docker buildx build \
  --platform linux/amd64 \
  --tag ghcr.io/YOUR_GITHUB_USER/router-agent-track1:latest \
  --push .
```

## Local Container Test

Create local fixtures:

```bash
mkdir -p local_input local_output
cat > local_input/tasks.json <<'JSON'
[
  {"task_id": "m1", "prompt": "What is 2 + 2?"},
  {"task_id": "s1", "prompt": "Classify the sentiment: I loved this workshop."}
]
JSON
```

Run with a mock Fireworks model:

```bash
docker run --rm \
  -e ALLOW_DEV_MOCK=1 \
  -e ALLOWED_MODELS=mock-remote-model \
  -e FIREWORKS_API_KEY=dev \
  -e FIREWORKS_BASE_URL=http://mock.local/v1 \
  -v "$PWD/local_input:/input:ro" \
  -v "$PWD/local_output:/output" \
  YOUR_IMAGE:latest
```

Inspect:

```bash
cat local_output/results.json
```

## Size Notes

The image uses `python:3.12-slim`, CPU PyTorch wheels, `PIP_NO_CACHE_DIR=1`, a
multi-stage Hugging Face cache, and removes Python `__pycache__` directories.
It should remain well below the 10GB compressed image limit.
