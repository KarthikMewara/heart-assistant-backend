import json

from app.config import BASE_DIR

RANGES = json.loads((BASE_DIR / "data" / "reference_ranges.json").read_text())
SEVERITY = {"normal": 0, "borderline": 1, "high": 2, "critical": 3}

CATEGORICAL_FLAGS = {
    ("resting_ecg", "ST"): ("ECG", "borderline", "ST-T changes on ECG: discuss with a cardiologist"),
    ("resting_ecg", "LVH"): ("ECG", "borderline", "Thickened heart wall on ECG: discuss with a cardiologist"),
    ("st_slope", "Flat"): ("Treadmill ST slope", "borderline", "Flat ST slope during exercise"),
    ("st_slope", "Down"): ("Treadmill ST slope", "high", "Downsloping ST during exercise"),
    ("exercise_angina", True): ("Chest pain on exercise", "high", "Chest pain during exertion needs a doctor's review"),
}


def flag_values(values: dict) -> list[dict]:
    flags = []
    for field, rule in RANGES.items():
        if field not in values:
            continue
        value = values[field]
        band = next(b for b in rule["bands"] if b["max"] is None or value < b["max"])
        flags.append({"field": field, "label": rule["label"], "value": value, "unit": rule["unit"],
                      "status": band["status"], "note": band["note"]})
    for (field, match), (label, status, note) in CATEGORICAL_FLAGS.items():
        if values.get(field) == match:
            flags.append({"field": field, "label": label, "value": match, "unit": "",
                          "status": status, "note": note})
    return sorted(flags, key=lambda f: -SEVERITY[f["status"]])


def is_urgent(flags: list[dict]) -> bool:
    return any(f["status"] == "critical" for f in flags)