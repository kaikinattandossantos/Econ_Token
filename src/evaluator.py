import re
from .task_types import Task

def estimate_task_difficulty(task_content: str) -> float:
    """Estimate task difficulty from 0.0 to 1.0."""
    score = 0.0
    
    # Heuristics
    complex_keywords = ["prove", "calculate", "debug", "optimize", "legal", "medical", "financial", "step by step"]
    if any(word in task_content.lower() for word in complex_keywords):
        score += 0.4
        
    if len(task_content.split()) > 50:
        score += 0.2
        
    if re.search(r"```[a-z]*\n", task_content): # Presence of code
        score += 0.3
        
    if "?" in task_content and task_content.count("?") > 2: # Multiple questions
        score += 0.2
        
    return min(score, 1.0)

def estimate_local_confidence(task_content: str, answer: str) -> float:
    """Estimate confidence in the local answer."""
    if not answer or len(answer.strip()) < 5:
        return 0.0
    
    if "error calling local model" in answer.lower():
        return 0.0
        
    # Simple heuristic: if local answer is much shorter than input for complex tasks
    if len(task_content) > 100 and len(answer) < 20:
        return 0.3
        
    return 0.8 # Default baseline

def should_escalate(task: Task, local_answer: str, confidence: float, threshold: float = 0.7) -> bool:
    """Decide if the task should be escalated to remote."""
    if confidence < 0.3: # Hard fail
        return True
    
    if confidence < threshold:
        return True
        
    return False
