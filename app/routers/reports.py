import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Report, User
from app.schemas import ReportOut, ReportValues
from app.security import get_current_user
from app.services.extraction import extract_text
from app.services.parser import parse_report

router = APIRouter(prefix="/reports", tags=["reports"])
ALLOWED = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_BYTES = 10 * 1024 * 1024


def _out(report: Report, needs_review: list[str] | None = None) -> ReportOut:
    missing = [f for f in ReportValues.model_fields if f not in report.values]
    return ReportOut.model_validate(report).model_copy(
        update={"needs_review": needs_review or [], "missing": missing})


def _own(db: Session, report_id: int, user: User) -> Report:
    report = db.get(Report, report_id)
    if report is None or report.user_id != user.id:
        raise HTTPException(404, "Report not found")
    return report


@router.post("/upload", response_model=ReportOut, status_code=201)
async def upload(file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Upload a PDF, PNG or JPG file")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(400, "File is larger than 10 MB")

    folder = settings.upload_dir / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(content)

    text = extract_text(path)
    parsed = parse_report(text)
    report = Report(user_id=user.id, filename=file.filename, file_path=str(path),
                    raw_text=text, values=parsed["values"])
    db.add(report)
    db.commit()
    db.refresh(report)
    return _out(report, parsed["needs_review"])


@router.post("/manual", response_model=ReportOut, status_code=201)
def manual(values: ReportValues, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = Report(user_id=user.id, filename="manual entry", file_path="",
                    values=values.model_dump(exclude_none=True), confirmed=True)
    db.add(report)
    db.commit()
    db.refresh(report)
    return _out(report)


@router.put("/{report_id}/values", response_model=ReportOut)
def confirm_values(report_id: int, values: ReportValues, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    report = _own(db, report_id, user)
    report.values = values.model_dump(exclude_none=True)
    report.confirmed = True
    db.commit()
    db.refresh(report)
    return _out(report)


@router.get("", response_model=list[ReportOut])
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reports = db.query(Report).filter_by(user_id=user.id).order_by(Report.created_at.desc()).all()
    return [_out(r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(_own(db, report_id, user))