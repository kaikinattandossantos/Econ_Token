from enum import Enum
from dataclasses import dataclass
from typing import Optional

class TaskDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Route(Enum):
    LOCAL = "local"
    LOCAL_COMPETITION = "local_competition"
    REMOTE = "remote"

@dataclass
class Task:
    content: str
    id: Optional[str] = None
    difficulty_hint: Optional[TaskDifficulty] = None
