FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DISABLE_DOTENV=1 \
    INPUT_PATH=/input/tasks.json \
    OUTPUT_PATH=/output/results.json \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY scripts/download_hf_models.py ./scripts/download_hf_models.py

# Pre-cache semantic-router embeddings so container startup stays under 60s.
RUN python scripts/download_hf_models.py

RUN python -m compileall -q src

CMD ["python", "-m", "src.submission"]