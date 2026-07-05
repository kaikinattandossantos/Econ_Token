# Prompts for the agent

CLASSIFICATION_PROMPT = """Analyze the following task and classify its difficulty and type.
Task: {task}

Output only a JSON with 'difficulty' (easy, medium, hard) and 'type' (coding, math, reasoning, extraction, summary).
"""

LOCAL_SYSTEM_PROMPT = "You are a helpful and efficient local assistant. Be concise."
REMOTE_SYSTEM_PROMPT = "You are a highly capable remote AI assistant. Provide accurate and detailed answers."
