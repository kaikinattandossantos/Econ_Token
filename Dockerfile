# syntax=docker/dockerfile:1

# Stage 1: download HuggingFace / sentence-transformers weights at build time only.
FROM python:3.12-slim AS model-cache

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache \
    TRANSFORMERS_CACHE=/opt/hf-cache \
    SENTENCE_TRANSFORMERS_HOME=/opt/hf-cache

WORKDIR /build

COPY requirements.txt ./
RUN pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY scripts/download_hf_models.py ./scripts/download_hf_models.py
RUN python scripts/download_hf_models.py

# Stage 2: lean runtime image — no network needed for embeddings.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DISABLE_DOTENV=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/huggingface \
    INPUT_PATH=/input/tasks.json \
    OUTPUT_PATH=/output/results.json

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir \
        torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && find /usr/local/lib/python3.12 -type d -name __pycache__ -prune -exec rm -rf {} +

COPY --from=model-cache /opt/hf-cache /app/.cache/huggingface

COPY src ./src

RUN python -m compileall -q src

ENTRYPOINT ["python", "-m", "src.submission"]