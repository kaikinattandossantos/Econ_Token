# Hybrid Token-Efficient Routing Agent


## Project Description

This project aims to build an AI agent capable of completing tasks by intelligently deciding whether to use a deterministic rule, a local language model (via Ollama), or a remote, more powerful model (via Fireworks AI). The primary objective is to minimize the use of expensive remote tokens while maintaining high accuracy. This hybrid approach handles very simple tasks without model calls, leverages local resources for low-risk tasks, and escalates to remote models only when necessary.

## Project Structure

```
router_agent/
  README.md
  requirements.txt
  .env.example
  src/
    main.py
    config.py
    router.py
    specialist_agents.py
    template_responder.py
    deterministic_tools.py
    local_model.py
    remote_fireworks.py
    evaluator.py
    task_types.py
    prompts.py
    logging_utils.py
  data/
    examples.jsonl
  logs/
    .gitkeep
  tests/
    test_router.py
    test_evaluator.py
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Docker (for Ollama)

### 1. Install Dependencies

```bash
pip install -r requirements-dev.txt
```

For the submission Docker image only, use the lean `requirements.txt` (handled automatically by the Dockerfile).

This installs `sentence-transformers`, which enables the optional Hugging Face semantic router. The default model is:

```ini
SEMANTIC_ROUTER_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Use it for Portuguese and multilingual tasks. For a faster English-oriented model, set:

```ini
SEMANTIC_ROUTER_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The model is downloaded on first use and cached locally by Hugging Face.

To pre-download and smoke test both Hugging Face models:

```bash
python scripts/download_hf_models.py
```

### 2. Install Ollama and Download Local Model

If you don't have Ollama installed, follow the instructions for your operating system:

- **Windows**: Download the installer from [Ollama's official website](https://ollama.com/download/windows). After installation, open PowerShell or Command Prompt and run:
  ```bash
  ollama pull qwen2.5:0.5b
  ```
- **Linux/macOS**: Follow the instructions on [Ollama's website](https://ollama.com/download).
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ollama pull qwen2.5:0.5b
  ```

Ensure Ollama is running in the background. By default, it listens on `http://localhost:11434`.

### 3. Configure Environment Variables

Copy the example environment file and fill in your Fireworks AI API key:

```bash
cp .env.example .env
```

Edit the newly created `.env` file:

```ini
# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434/api/generate
LOCAL_MODEL_NAME=qwen2.5:0.5b

# Fireworks AI Settings
FIREWORKS_API_KEY=your_fireworks_api_key_here  # Get your API key from Fireworks AI
REMOTE_MODEL_NAME=accounts/fireworks/models/llama-v3p1-70b-instruct

# Strategy Settings
ENABLE_LOCAL_COMPETITION=false
ROUTING_THRESHOLD=0.7
```

If `FIREWORKS_API_KEY` is not provided, the remote model integration will use a mock response for development and testing purposes.

## Usage

### Run a single task

```bash
python -m src.main --task "Explain token-efficient routing in AI agents."
```

### Run tasks from a file

```bash
python -m src.main --file data/examples.jsonl
```

### Output Example

```
[ROUTE]: LOCAL
[CONFIDENCE]: 0.80
[REMOTE TOKENS]: 0
[ANSWER]:
Token-efficient routing in AI agents refers to the strategy of intelligently directing tasks to different language models (LMs) based on their complexity and cost, aiming to minimize the usage of expensive, high-token-count remote models. This typically involves using smaller, local LMs for simpler tasks and escalating to larger, remote LMs only when necessary, thereby optimizing cost and efficiency.
```

## Routing Strategy

The `HybridRouter` class in `src/router.py` is responsible for deciding whether to use a template response, a local model, or a remote model. The decision is based on a cheap local specialist pipeline:

1.  **Specialist Agents**: `specialist_agents.py` runs small deterministic passes for intent, entities, risk, answer contract, and routing. It creates a compact `TaskProfile` with task type, domain, risk, local fit, template fit, expected answer shape, constraints, and signals.
2.  **Semantic Router**: `semantic_router.py` optionally uses Hugging Face `sentence-transformers` embeddings to classify the task against route prototypes. It defaults to `paraphrase-multilingual-MiniLM-L12-v2`, with `all-MiniLM-L6-v2` as a faster fallback.
3.  **Template Agent**: `template_responder.py` handles cheap structured tasks such as counting ranges, simple arithmetic, known estimates, and parameterized fitness plans. These cost zero model tokens.
4.  **Compressed Local/Remote Prompts**: The router builds short prompts from the `TaskProfile`, so local and remote models receive only the task plus the answer contract instead of verbose instructions.
5.  **Task Difficulty and Verification**: `evaluator.py` estimates difficulty and checks whether a local answer fits the task. Bad local answers are escalated to remote.
6.  **Local Competition (Optional)**: If `ENABLE_LOCAL_COMPETITION` is set to `true`, the system can generate multiple local responses with slightly different prompts and compare them. If both responses are poor or divergent, it may trigger a remote call.

All routing decisions and outcomes are logged in `logs/runs.jsonl` for analysis.

## Testing

To run the tests, use `pytest`:

```bash
pytest tests/
```

Tests cover:
-   Difficulty estimation logic.
-   Escalation logic based on confidence.
-   Mock remote model behavior when `FIREWORKS_API_KEY` is not set.

## Hackathon Strategy

To evolve this project for the hackathon and maximize your score, consider the following steps:

-   **Calibrate Thresholds with Local Evaluation**: Systematically test different `ROUTING_THRESHOLD` values. Use a diverse set of tasks and evaluate the performance (accuracy vs. remote token usage) locally to find the optimal balance. This can be done by running tasks with varying thresholds and analyzing the `logs/runs.jsonl` output.
-   **Create a Dataset of Easy/Medium/Difficult Tasks**: Develop a comprehensive dataset of tasks categorized by difficulty. This dataset will be crucial for training and fine-tuning your `evaluator.py` heuristics and for robustly testing the router's decision-making.
-   **Measure Remote Escalation Rate**: Track the percentage of tasks that are escalated to the remote model. Your goal is to minimize this rate while maintaining acceptable accuracy. This metric will directly impact your token usage score.
-   **Compare Local vs. Remote Accuracy**: For a subset of tasks, run them through both local and remote models (even if the router decides local). Compare the accuracy of the local model's output against the remote model's output to understand the performance gap and refine your escalation logic.
-   **Reduce Remote Prompt to Minimum Necessary**: When a task is routed to the remote model, ensure the prompt sent is as concise and token-efficient as possible. Avoid sending unnecessary context or instructions that were already handled locally. This directly reduces remote token consumption.
-   **Use Local RAG Only When Corpus/Documents Provided**: Implement Retrieval-Augmented Generation (RAG) using local models only when there is a specific corpus of documents provided for the task. Avoid general web searches or large external knowledge bases with local RAG, as this can be inefficient. Focus on targeted information retrieval from provided context.

By focusing on these areas, you can systematically improve the agent's efficiency and accuracy, leading to a stronger performance in the hackathon. 

---

**Author**: Manus AI
