import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .router import HybridRouter

app = FastAPI(title="Router Agent API", version="1.0.0")
router = HybridRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    answer: str
    route: str
    difficulty_score: float
    local_confidence: float
    local_model: str
    remote_model: str
    usage: dict


session_stats = {
    "total_tokens": 0,
    "total_credits": 0.0,
    "local_tokens": 0,
    "remote_tokens": 0,
    "messages": 0,
}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stats")
def get_stats():
    total = session_stats["total_tokens"]
    local_pct = round((session_stats["local_tokens"] / total) * 100, 1) if total else 0.0
    remote_pct = round((session_stats["remote_tokens"] / total) * 100, 1) if total else 0.0

    return {
        **session_stats,
        "token_breakdown": [
            {
                "label": "Modelo Local",
                "tokens": session_stats["local_tokens"],
                "percentage": local_pct,
                "credits": 0.0,
                "credit_percentage": 0.0,
            },
            {
                "label": "Modelo Remoto",
                "tokens": session_stats["remote_tokens"],
                "percentage": remote_pct,
                "credits": session_stats["total_credits"],
                "credit_percentage": 100.0 if session_stats["total_credits"] > 0 else 0.0,
            },
        ],
    }


@app.post("/api/stats/reset")
def reset_stats():
    session_stats.update({
        "total_tokens": 0,
        "total_credits": 0.0,
        "local_tokens": 0,
        "remote_tokens": 0,
        "messages": 0,
    })
    return {"status": "reset"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = router.run(request.message, task_id=request.conversation_id or "default")

    usage = result["usage"]
    session_stats["total_tokens"] += usage["tokens"]["total"]
    session_stats["local_tokens"] += usage["tokens"]["local_total"]
    session_stats["remote_tokens"] += usage["tokens"]["remote_total"]
    session_stats["total_credits"] += usage["credits"]["total_spent"]
    session_stats["messages"] += 1

    return ChatResponse(
        answer=result["answer"],
        route=result["route"],
        difficulty_score=result["difficulty_score"],
        local_confidence=result["local_confidence"],
        local_model=result["local_model"],
        remote_model=result["remote_model"],
        usage=usage,
    )


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")