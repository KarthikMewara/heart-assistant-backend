import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.models import User
from app.security import get_current_user
from app.services.parser import parse_report
from app.services.speech import transcribe

router = APIRouter(prefix="/voice", tags=["voice"])


async def _transcribe_upload(audio: UploadFile) -> str:
    suffix = Path(audio.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
    try:
        text = transcribe(Path(tmp.name))
    finally:
        Path(tmp.name).unlink(missing_ok=True)      # audio is never kept
    if not text:
        raise HTTPException(422, "Sorry, I could not hear anything. Please try again.")
    return text


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile, user: User = Depends(get_current_user)):
    return {"text": await _transcribe_upload(audio)}


@router.post("/values")
async def values_from_speech(audio: UploadFile, user: User = Depends(get_current_user)):
    text = await _transcribe_upload(audio)
    parsed = parse_report(text)
    return {"text": text, "values": parsed["values"], "needs_review": parsed["needs_review"]}