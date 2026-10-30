import re

NUMBER = r"(\d+(?:\.\d+)?)"
GAP = r"[^\d\n]{0,30}?"     # allows words like "(mg/dL) :" between name and number

ALIASES = {
    "total_cholesterol": [r"total\s+cholesterol", r"cholesterol[,\s]+total", r"serum\s+cholesterol",
                          r"(?<!ldl )(?<!hdl )(?<!ldl-)(?<!hdl-)\bcholesterol\b"],   # plain "cholesterol", e.g. spoken
    "ldl": [r"\bldl(?:[\s-]*(?:cholesterol|c))?\b"],
    "hdl": [r"\bhdl(?:[\s-]*(?:cholesterol|c))?\b"],
    "triglycerides": [r"triglycerides?"],
    "fasting_glucose": [r"fasting\s+(?:blood\s+)?(?:glucose|sugar)", r"\bfbs\b"],
    "hba1c": [r"hba1c", r"glycated\s+ha?emoglobin"],
    "heart_rate": [r"heart\s+rate", r"pulse(?:\s+rate)?"],
    "max_hr": [r"max(?:imum)?\.?\s+(?:heart\s+rate|hr)", r"peak\s+(?:heart\s+rate|hr)"],
    "oldpeak": [r"st\s+depression"],
    "troponin": [r"troponin(?:[\s-]*[it])?"],
}

PLAUSIBLE = {
    "total_cholesterol": (50, 600), "ldl": (10, 400), "hdl": (5, 150), "triglycerides": (20, 2000),
    "fasting_glucose": (30, 600), "hba1c": (3, 20), "heart_rate": (25, 220), "max_hr": (60, 220),
    "oldpeak": (0, 7), "troponin": (0, 100), "systolic_bp": (60, 260), "diastolic_bp": (30, 160),
}

BP_PATTERN = re.compile(r"(?:blood\s+pressure|\bbp\b)" + GAP + r"(\d{2,3})\s*(?:/|over|by)\s*(\d{2,3})", re.I)

def parse_report(text: str) -> dict:
    values: dict = {}
    for line in text.splitlines():
        for field, patterns in ALIASES.items():
            if field in values:
                continue
            if field == "heart_rate" and re.search(r"max|peak|target", line, re.I):
                continue                     # that line is the treadmill peak, not resting rate
            for pattern in patterns:
                match = re.search(pattern + GAP + NUMBER, line, re.I)
                if match:
                    values[field] = float(match.group(1))
                    break
        if "systolic_bp" not in values and (bp := BP_PATTERN.search(line)):
            values["systolic_bp"], values["diastolic_bp"] = float(bp.group(1)), float(bp.group(2))

    values.update(_categorical(text))
    rejected = [f for f, v in values.items() if f in PLAUSIBLE and not PLAUSIBLE[f][0] <= v <= PLAUSIBLE[f][1]]
    for field in rejected:
        values.pop(field)
    return {"values": values, "needs_review": rejected}


def _categorical(text: str) -> dict:
    found = {}
    if re.search(r"\blvh\b|left\s+ventricular\s+hypertrophy", text, re.I):
        found["resting_ecg"] = "LVH"
    elif re.search(r"st[\s-]*t\s+(?:wave\s+)?changes?|st\s+elevation|t[\s-]wave\s+inversion", text, re.I):
        found["resting_ecg"] = "ST"
    elif re.search(r"normal\s+sinus\s+rhythm|ecg\s+within\s+normal\s+limits", text, re.I):
        found["resting_ecg"] = "Normal"
    if slope := re.search(r"\b(up|down)[\s-]?sloping\b|\bflat\s+st\b|st\s+segment\s+flat", text, re.I):
        found["st_slope"] = (slope.group(1) or "flat").capitalize()
    return found