from fastapi import APIRouter

from app.services.risk_model import METRICS

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/model/metrics")
def model_metrics():
    return METRICS