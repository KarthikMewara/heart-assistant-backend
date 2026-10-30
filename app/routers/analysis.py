from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis, Report, User
from app.schemas import AnalysisOut
from app.security import get_current_user
from app.services.flags import flag_values, is_urgent
from app.services.risk_model import assess
from app.services.llm import generate_plan

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _out(analysis: Analysis, completeness: float | None = None) -> AnalysisOut:
    return AnalysisOut.model_validate(analysis).model_copy(
        update={"urgent": is_urgent(analysis.flags), "completeness": completeness})


def _own(db: Session, analysis_id: int, user: User) -> Analysis:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None or analysis.user_id != user.id:
        raise HTTPException(404, "Analysis not found")
    return analysis


@router.post("/report/{report_id}", response_model=AnalysisOut, status_code=201)
def analyse_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.get(Report, report_id)
    if report is None or report.user_id != user.id:
        raise HTTPException(404, "Report not found")
    if not report.confirmed:
        raise HTTPException(400, "Please check and confirm the report values first")
    if user.age is None or user.sex is None:
        raise HTTPException(400, "Please add age and sex to your profile first")

    flags = flag_values(report.values)
    result = assess(report.values, user.age, user.sex)
    analysis = Analysis(user_id=user.id, report_id=report.id, inputs=report.values, flags=flags,
                        risk_score=result["risk_score"], risk_level=result["risk_level"],
                        reasons=result["reasons"])
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _out(analysis, result["completeness"])

@router.post("/{analysis_id}/plan", response_model=AnalysisOut)
def create_plan(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    analysis = _own(db, analysis_id, user)
    plan, source = generate_plan(analysis.flags, analysis.reasons, analysis.risk_level,
                                 user.age, is_urgent(analysis.flags))
    analysis.plan = {**plan, "source": source}     # "llm" or "fallback", useful for your report
    db.commit()
    db.refresh(analysis)
    return _out(analysis)


@router.get("", response_model=list[AnalysisOut])
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Analysis).filter_by(user_id=user.id).order_by(Analysis.created_at).all()
    return [_out(a) for a in rows]          # oldest first, ready for a trend chart


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(_own(db, analysis_id, user))


