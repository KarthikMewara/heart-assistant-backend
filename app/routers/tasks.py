from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TaskCompletion, User
from app.security import get_current_user
from app.services.daily_tasks import streak, tasks_for

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/today")
def today_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    completions = db.query(TaskCompletion).filter_by(user_id=user.id).all()
    done_today = {c.task_id for c in completions if c.done_on == today}
    tasks = [{**t, "done": t["id"] in done_today} for t in tasks_for(user.id, today)]
    return {"date": today, "tasks": tasks, "streak": streak({c.done_on for c in completions}, today)}


@router.post("/{task_id}/complete", status_code=201)
def complete_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    if task_id not in {t["id"] for t in tasks_for(user.id, today)}:
        raise HTTPException(400, "That task is not on today's list")
    exists = db.query(TaskCompletion).filter_by(user_id=user.id, task_id=task_id, done_on=today).first()
    if not exists:
        db.add(TaskCompletion(user_id=user.id, task_id=task_id, done_on=today))
        db.commit()
    return today_tasks(db, user)