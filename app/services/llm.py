import json
import re

import httpx
from pydantic import BaseModel, ValidationError

from app.config import BASE_DIR, settings

GUIDANCE_FILE = BASE_DIR / "data" / "guidance" / "heart_guidance.md"
SECTIONS = dict(re.findall(r"^## (\w+)\n(.*?)(?=^## |\Z)", GUIDANCE_FILE.read_text(), re.S | re.M))

# Which guidance section to retrieve for each flagged value
FIELD_TO_SECTION = {
    "total_cholesterol": "high_cholesterol", "ldl": "high_cholesterol", "hdl": "low_hdl",
    "triglycerides": "high_triglycerides", "systolic_bp": "high_bp", "diastolic_bp": "high_bp",
    "fasting_glucose": "high_sugar", "hba1c": "high_sugar", "heart_rate": "heart_rhythm",
    "exercise_angina": "exercise_caution", "oldpeak": "exercise_caution", "st_slope": "exercise_caution",
}
UNSAFE = re.compile(r"stop taking|increase (?:your|the) dose|reduce (?:your|the) dose|instead of (?:your )?medicine", re.I)


class SampleDay(BaseModel):
    breakfast: str
    lunch: str
    evening_snack: str
    dinner: str


class Plan(BaseModel):
    summary: str
    eat_more: list[str]
    limit: list[str]
    sample_day: SampleDay
    exercise: list[str]
    lifestyle: list[str]
    see_doctor: str
    speak_text: str          # a short, friendly version for read-aloud


def retrieve(flags: list[dict]) -> list[str]:
    keys = ["general"] + [FIELD_TO_SECTION[f["field"]] for f in flags
                          if f["status"] != "normal" and f["field"] in FIELD_TO_SECTION]
    return list(dict.fromkeys(keys))          # unique, in order


def build_prompt(flags, reasons, risk_level, age, urgent, sections) -> str:
    problems = [f"- {f['label']}: {f['value']} {f['unit']} ({f['note']})" for f in flags if f["status"] != "normal"]
    guidance = "\n\n".join(SECTIONS[s].strip() for s in sections)
    return f"""You are a kind health guide for an elderly person in India, aged {age}.
You are not a doctor. Never diagnose, never mention medicine names or doses, and never tell them to stop or change medicines.
Use only the guidance below. Use simple words and short sentences. Suggest Indian home foods.

Their results:
{chr(10).join(problems) or '- All values are in the normal range.'}
Heart risk level from our model: {risk_level}. Main factors: {', '.join(r['factor'] for r in reasons) or 'none'}.
{'Some values are dangerous: the summary and see_doctor must tell them to contact a doctor today.' if urgent else ''}

Trusted guidance:
{guidance}

Reply with JSON only, with exactly these keys:
summary (2 sentences), eat_more (list of 4 to 6), limit (list of 4 to 6),
sample_day (object with breakfast, lunch, evening_snack, dinner), exercise (list of 2 to 4),
lifestyle (list of 2 to 4), see_doctor (1 sentence), speak_text (under 80 words, warm and simple)."""


def generate_plan(flags, reasons, risk_level, age, urgent) -> tuple[dict, str]:
    sections = retrieve(flags)
    prompt = build_prompt(flags, reasons, risk_level, age, urgent, sections)
    try:
        response = httpx.post(f"{settings.ollama_url}/api/chat", timeout=180, json={
            "model": settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json", "stream": False, "options": {"temperature": 0.3},
        })
        response.raise_for_status()
        content = response.json()["message"]["content"]
        if UNSAFE.search(content):
            raise ValueError("unsafe medicine advice")
        return Plan.model_validate(json.loads(content)).model_dump(), "llm"
    except (httpx.HTTPError, ValidationError, ValueError, KeyError) as error:
        print("LLM failed, using fallback:", error)
        return fallback_plan(sections, urgent), "fallback"


def fallback_plan(sections: list[str], urgent: bool) -> dict:
    tips = [line.strip() for s in sections for line in SECTIONS[s].strip().splitlines()]
    doctor = ("Some results need attention today. Please contact your doctor or call 112." if urgent
              else "Share these results with your doctor at your next visit.")
    return Plan(
        summary="Here are general heart-healthy steps based on your report.",
        eat_more=tips[:3], limit=tips[3:5] or ["Fried and very salty foods"],
        sample_day=SampleDay(breakfast="Vegetable oats or poha with sprouts", lunch="Two whole wheat rotis, dal, sabzi, salad",
                             evening_snack="A fruit and a few unsalted almonds", dinner="Millet khichdi with vegetables and curd"),
        exercise=["Walk slowly for 20 to 30 minutes on most days"],
        lifestyle=["Sleep 7 to 8 hours", "Avoid tobacco"],
        see_doctor=doctor, speak_text=f"Your report is ready. {doctor} Eat simple home food with less salt and oil, and walk every day.",
    ).model_dump()