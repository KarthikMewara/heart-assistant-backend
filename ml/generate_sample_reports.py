"""Create sample heart reports with known values. Run: python -m ml.generate_sample_reports"""
import json
import random
from pathlib import Path

import pymupdf as fitz

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_reports"
LABS = ["City Diagnostics", "Sunrise Pathology Lab", "HeartCare Clinic"]


def random_values() -> dict:
    return {
        "total_cholesterol": random.randint(140, 320), "ldl": random.randint(70, 220),
        "hdl": random.randint(28, 75), "triglycerides": random.randint(80, 400),
        "fasting_glucose": random.randint(75, 220), "heart_rate": random.randint(55, 105),
        "systolic_bp": random.randint(105, 185), "diastolic_bp": random.randint(65, 110),
    }


def write_report(path: Path, v: dict) -> None:
    lines = [random.choice(LABS), "Patient: Sample Patient    Age: 68", "",
             "LIPID PROFILE", f"Total Cholesterol : {v['total_cholesterol']} mg/dL   (Desirable < 200)",
             f"LDL Cholesterol : {v['ldl']} mg/dL", f"HDL Cholesterol : {v['hdl']} mg/dL",
             f"Triglycerides : {v['triglycerides']} mg/dL", "", "BLOOD SUGAR",
             f"Fasting Blood Sugar : {v['fasting_glucose']} mg/dL", "", "VITALS",
             f"Blood Pressure : {v['systolic_bp']}/{v['diastolic_bp']} mm Hg",
             f"Pulse Rate : {v['heart_rate']} bpm"]
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((60, 70), "\n".join(lines), fontsize=11, lineheight=1.6)
    pdf.save(path.with_suffix(".pdf"))
    page.get_pixmap(dpi=150).save(path.with_suffix(".png"))   # image version tests OCR
    pdf.close()


def main(count: int = 30) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    truth = {}
    for i in range(count):
        values = random_values()
        write_report(OUT / f"report_{i:02d}", values)
        truth[f"report_{i:02d}"] = values
    (OUT / "ground_truth.json").write_text(json.dumps(truth, indent=2))


if __name__ == "__main__":
    main()