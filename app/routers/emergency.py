import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmergencyEvent, User
from app.security import get_current_user

router = APIRouter(prefix="/emergency", tags=["emergency"])
RED_FLAGS = re.compile(r"chest\s+pain|can'?t\s+breathe|short(?:ness)?\s+of\s+breath|faint|unconscious|"
                       r"left\s+arm|jaw\s+pain|severe\s+headache|slurred|face\s+droop|collapse", re.I)


class EmergencyIn(BaseModel):
    reason: str = "SOS button pressed"


class TextIn(BaseModel):
    text: str


@router.post("")
def trigger(body: EmergencyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(EmergencyEvent(user_id=user.id, reason=body.reason))
    db.commit()
    return {
        "message": "Stay calm. Call for help now. If you have chest pain, sit down and do not walk around.",
        "call": [{"name": "Emergency", "number": "112"}, {"name": "Ambulance", "number": "108"}],
        "caregiver": {"name": user.caregiver_name, "phone": user.caregiver_phone},
    }


@router.post("/check")
def check_text(body: TextIn, user: User = Depends(get_current_user)):
    found = sorted({m.group(0).lower() for m in RED_FLAGS.finditer(body.text)})
    return {"is_emergency": bool(found), "matched": found}