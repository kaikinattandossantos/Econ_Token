"""Bridge from TaskProfile to deterministic solvers (Rule 6).

Template/canned factual answers were removed. Only try_deterministic is used so
unseen evaluation variants are never answered from hardcoded lookup tables.
"""

from __future__ import annotations

from typing import Optional

from .deterministic_tools import DeterministicResult, try_deterministic
from .specialist_agents import TaskProfile


def try_template_response(profile: TaskProfile) -> Optional[DeterministicResult]:
    """Attempt a zero-token solve before any Fireworks call."""
    return try_deterministic(profile.raw_task)