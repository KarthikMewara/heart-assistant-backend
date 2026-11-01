from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import analysis, assistant, auth, emergency, meta, reminders, reports, tasks, voice
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Heart Health Assistant API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(analysis.router)
app.include_router(voice.router)
app.include_router(reminders.router)
app.include_router(tasks.router)
app.include_router(emergency.router)
app.include_router(meta.router)
app.include_router(assistant.router)