"""Measure how often values are read correctly from sample reports. Run: python -m ml.evaluate_extraction"""
import json
from pathlib import Path

from app.services.extraction import extract_text
from app.services.parser import parse_report

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "sample_reports"


def main():
    truth = json.loads((SAMPLES / "ground_truth.json").read_text())
    results = {}
    for suffix in (".pdf", ".png"):
        correct = total = 0
        for name, expected in truth.items():
            found = parse_report(extract_text(SAMPLES / f"{name}{suffix}"))["values"]
            for field, value in expected.items():
                total += 1
                correct += abs(found.get(field, -1) - value) < 0.01
        results[suffix] = round(correct / total, 3)
        print(f"{suffix}: {correct}/{total} values correct ({correct / total:.1%})")
    (Path(__file__).parent / "artifacts" / "extraction_metrics.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()