from datetime import date, timedelta

from app.services.daily_tasks import streak, tasks_for
from app.services.flags import flag_values, is_urgent
from app.services.parser import parse_report


def test_parses_lipid_and_bp():
    text = "Total Cholesterol : 245 mg/dL\nHDL Cholesterol : 38 mg/dL\nBlood Pressure : 150/95 mm Hg"
    values = parse_report(text)["values"]
    assert values == {"total_cholesterol": 245, "hdl": 38, "systolic_bp": 150, "diastolic_bp": 95}


def test_spoken_values():
    values = parse_report("my blood pressure is 140 over 90 and my cholesterol is 230")["values"]
    assert values["systolic_bp"] == 140 and values["total_cholesterol"] == 230


def test_rejects_impossible_numbers():
    assert "total_cholesterol" in parse_report("Total Cholesterol : 2450")["needs_review"]


def test_very_high_bp_is_urgent():
    flags = flag_values({"systolic_bp": 190})
    assert flags[0]["status"] == "critical" and is_urgent(flags)


def test_low_hdl_is_flagged():
    assert flag_values({"hdl": 35})[0]["status"] == "high"


def test_daily_tasks_are_stable_for_a_day():
    today = date(2026, 10, 30)
    assert tasks_for(1, today) == tasks_for(1, today)
    assert len(tasks_for(1, today)) == 4


def test_streak_counts_consecutive_days():
    today = date(2026, 10, 30)
    days = {today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=5)}
    assert streak(days, today) == 3