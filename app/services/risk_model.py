import json

import joblib
import numpy as np
import pandas as pd

from app.config import BASE_DIR

ARTIFACTS = BASE_DIR / "ml" / "artifacts"
MODEL = joblib.load(ARTIFACTS / "risk_model.joblib")
METRICS = json.loads((ARTIFACTS / "metrics.json").read_text())
REPORT_INPUTS = ["RestingBP", "Cholesterol", "FastingBS", "RestingECG", "MaxHR",
                 "ExerciseAngina", "Oldpeak", "ST_Slope", "ChestPainType"]

# What "healthy" looks like for each value a person can improve, with a plain-language name
HEALTHY = {
    "RestingBP": (120, "blood pressure"),
    "Cholesterol": (180, "cholesterol"),
    "FastingBS": (0, "blood sugar"),
    "Oldpeak": (0.0, "treadmill ST depression"),
    "ExerciseAngina": ("N", "chest pain during exercise"),
    "ST_Slope": ("Up", "treadmill ST slope"),
    "RestingECG": ("Normal", "ECG changes"),
}


def to_features(values: dict, age: int, sex: str) -> dict:
    sugar = values.get("fasting_glucose")
    angina = values.get("exercise_angina")
    row = {
        "Age": age, "Sex": sex,
        "ChestPainType": values.get("chest_pain_type"),
        "RestingBP": values.get("systolic_bp"),
        "Cholesterol": values.get("total_cholesterol"),
        "FastingBS": None if sugar is None else int(sugar > 120),
        "RestingECG": values.get("resting_ecg"),
        "MaxHR": values.get("max_hr"),
        "ExerciseAngina": None if angina is None else ("Y" if angina else "N"),
        "Oldpeak": values.get("oldpeak"),
        "ST_Slope": values.get("st_slope"),
    }
    return {k: (np.nan if v is None else v) for k, v in row.items()}   # NaN lets the model fill gaps


def _predict(row: dict) -> float:
    return float(MODEL.predict_proba(pd.DataFrame([row], columns=METRICS["features"]))[0, 1])


def assess(values: dict, age: int, sex: str) -> dict:
    row = to_features(values, age, sex)
    risk = _predict(row)
    reasons = []
    for feature, (healthy, name) in HEALTHY.items():
        if pd.isna(row[feature]) or row[feature] == healthy:
            continue
        drop = risk - _predict({**row, feature: healthy})
        if drop >= 0.03:
            reasons.append({"factor": name, "impact": round(drop, 2)})
    reasons.sort(key=lambda r: -r["impact"])
    provided = sum(not pd.isna(row[f]) for f in REPORT_INPUTS)
    return {
        "risk_score": round(risk, 2),
        "risk_level": "low" if risk < 0.3 else "moderate" if risk < 0.6 else "high",
        "reasons": reasons,
        "completeness": round(provided / len(REPORT_INPUTS), 2),
    }