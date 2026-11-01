from typing import Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Analysis, User
from app.routers.emergency import RED_FLAGS
from app.security import get_current_user

router = APIRouter(prefix="/assistant", tags=["assistant"])


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[Turn] = []


@router.post("/chat")
def chat(body: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Safety first: emergency words skip the model entirely
    if RED_FLAGS.search(body.message):
        return {"reply": "This sounds serious. Please press the SOS button or call 112 now.", "emergency": True}

    latest = (db.query(Analysis).filter_by(user_id=user.id)
              .order_by(Analysis.created_at.desc()).first())
    context = "No report analysed yet."
    if latest:
        problems = [f"{f['label']} {f['value']} ({f['status']})" for f in latest.flags if f["status"] != "normal"]
        context = f"Latest heart risk: {latest.risk_level}. Problems: {', '.join(problems) or 'none'}."

    system = (f"You are AYURA, a kind health guide for {user.name}, aged {user.age}, in India. "
              "You are not a doctor: never diagnose, never name medicines or doses. "
              f"Answer in 2 to 4 short, simple sentences. {context}")
    messages = [{"role": "system", "content": system},
                *[t.model_dump() for t in body.history[-6:]],
                {"role": "user", "content": body.message}]
    try:
        r = httpx.post(f"{settings.ollama_url}/api/chat", timeout=120, json={
            "model": settings.ollama_model, "messages": messages,
            "stream": False, "options": {"temperature": 0.4}})
        r.raise_for_status()
        reply = r.json()["message"]["content"].strip()
    except (httpx.HTTPError, KeyError):
        reply = "Sorry, I can't think right now. Please try again in a minute."
    return {"reply": reply, "emergency": False}