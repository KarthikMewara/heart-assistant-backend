from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reminder, User
from app.schemas import ReminderIn, ReminderOut
from app.security import get_current_user

router = APIRouter(prefix="/reminders", tags=["reminders"])


def _own(db: Session, reminder_id: int, user: User) -> Reminder:
    reminder = db.get(Reminder, reminder_id)
    if reminder is None or reminder.user_id != user.id:
        raise HTTPException(404, "Reminder not found")
    return reminder


@router.get("", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Reminder).filter_by(user_id=user.id).order_by(Reminder.time_of_day).all()


@router.post("", response_model=ReminderOut, status_code=201)
def create_reminder(body: ReminderIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reminder = Reminder(user_id=user.id, **body.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, body: ReminderIn, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    reminder = _own(db, reminder_id, user)
    for key, value in body.model_dump().items():
        setattr(reminder, key, value)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(_own(db, reminder_id, user))
    db.commit()


@router.get("/due", response_model=list[ReminderOut])
def due_now(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Reminders whose time has passed today and that have not fired yet. Each fires once a day."""
    now, today = datetime.now().strftime("%H:%M"), date.today()
    due = [r for r in db.query(Reminder).filter_by(user_id=user.id, active=True).all()
           if r.time_of_day <= now and r.last_fired_on != today]
    for reminder in due:
        reminder.last_fired_on = today
    db.commit()
    return due