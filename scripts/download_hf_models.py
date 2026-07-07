from sentence_transformers import SentenceTransformer


MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/all-MiniLM-L6-v2",
]


def main():
    samples = [
        "conte de 0 a 10",
        "monte uma rotina de academia para biceps e triceps",
        "quantas pessoas vivem no brasil aproximadamente",
    ]
    for model_name in MODELS:
        print(f"Loading {model_name}...")
        model = SentenceTransformer(model_name)
        embeddings = model.encode(samples, normalize_embeddings=True)
        print(f"OK: {model_name} -> {embeddings.shape}")


if __name__ == "__main__":
    main()
