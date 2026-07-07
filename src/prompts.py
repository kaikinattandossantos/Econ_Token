# Prompts for the agent (Rule 1: English final answers)

CLASSIFICATION_PROMPT = """Analyze the following task and classify its difficulty and type.
Task: {task}

Output only a JSON with 'difficulty' (easy, medium, hard) and 'type' (one of:
factual_qa, math_reasoning, sentiment, summarization, ner, code_debugging,
logical_reasoning, code_generation).
"""

REMOTE_SYSTEM_PROMPT = (
    "You are a highly capable remote AI assistant. "
    "Provide accurate and detailed answers in English only."
)