from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Literal




class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str
    age: int | None = Field(default=None, ge=18, le=120)
    sex: str | None = Field(default=None, pattern="^(M|F)$")
    caregiver_name: str | None = None
    caregiver_phone: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    age: int | None
    sex: str | None
    caregiver_name: str | None
    caregiver_phone: str | None

class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = Field(default=None, ge=18, le=120)
    sex: str | None = Field(default=None, pattern="^(M|F)$")
    caregiver_name: str | None = None
    caregiver_phone: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"



class ReportValues(BaseModel):
    total_cholesterol: float | None = Field(None, ge=50, le=600, description="mg/dL")
    ldl: float | None = Field(None, ge=10, le=400, description="mg/dL")
    hdl: float | None = Field(None, ge=5, le=150, description="mg/dL")
    triglycerides: float | None = Field(None, ge=20, le=2000, description="mg/dL")
    systolic_bp: float | None = Field(None, ge=60, le=260, description="mm Hg")
    diastolic_bp: float | None = Field(None, ge=30, le=160, description="mm Hg")
    heart_rate: float | None = Field(None, ge=25, le=220, description="beats per minute, resting")
    fasting_glucose: float | None = Field(None, ge=30, le=600, description="mg/dL")
    hba1c: float | None = Field(None, ge=3, le=20, description="%")
    troponin: float | None = Field(None, ge=0, le=100, description="ng/mL")
    max_hr: float | None = Field(None, ge=60, le=220, description="peak in treadmill test")
    oldpeak: float | None = Field(None, ge=0, le=7, description="ST depression, mm")
    st_slope: Literal["Up", "Flat", "Down"] | None = None
    resting_ecg: Literal["Normal", "ST", "LVH"] | None = None
    chest_pain_type: Literal["ASY", "ATA", "NAP", "TA"] | None = None
    exercise_angina: bool | None = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    values: dict
    confirmed: bool
    created_at: datetime
    needs_review: list[str] = []
    missing: list[str] = []

class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int | None
    flags: list[dict]
    risk_score: float
    risk_level: str
    reasons: list[dict]
    plan: dict | None
    created_at: datetime
    urgent: bool = False
    completeness: float | None = None
    disclaimer: str = ("This is guidance, not a diagnosis. Please share these results with your doctor "
                       "before changing medicines, diet or exercise.")

class ReminderIn(BaseModel):
    title: str = Field(max_length=200)
    kind: Literal["medicine", "water", "walk", "appointment", "other"] = "medicine"
    time_of_day: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")      # "08:30"
    active: bool = True


class ReminderOut(ReminderIn):
    model_config = ConfigDict(from_attributes=True)
    id: int