"""Pre-download sentence-transformers models for offline Docker runtime."""

from __future__ import annotations

import os
import sys

from sentence_transformers import SentenceTransformer

MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/all-MiniLM-L6-v2",
]

SAMPLES = [
    "conte de 0 a 10",
    "monte uma rotina de academia para biceps e triceps",
    "quantas pessoas vivem no brasil aproximadamente",
]


def _cache_roots() -> list[str]:
    roots: list[str] = []
    for key in ("HF_HOME", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"):
        value = os.environ.get(key, "").strip()
        if value and value not in roots:
            roots.append(value)
    return roots


def main() -> int:
    print("Cache roots:", ", ".join(_cache_roots()) or "(default)")

    for model_name in MODELS:
        print(f"Downloading {model_name}...")
        model = SentenceTransformer(model_name)
        embeddings = model.encode(SAMPLES, normalize_embeddings=True)
        print(f"OK: {model_name} -> {embeddings.shape}")

    # Prove the cache is complete: reload with hub/network disabled.
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    for model_name in MODELS:
        print(f"Verifying offline load for {model_name}...")
        model = SentenceTransformer(model_name, local_files_only=True)
        embeddings = model.encode(SAMPLES[:1], normalize_embeddings=True)
        print(f"Offline OK: {model_name} -> {embeddings.shape}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())