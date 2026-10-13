import json
import pytest

from alert_escalation import AlertEscalationEngine
from longitudinal_tracker import LongitudinalTracker, load_from_csv


def test_alert_json_export(tmp_path):
    engine = AlertEscalationEngine("TEST-KEY")
    engine.evaluate_score(35)
    path = tmp_path / "alerts.json"
    engine.export_alerts_json(str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_alerts"] >= 1
    assert data["critical"] >= 1
    assert "Initiate prednisolone" not in data["alerts"][0]["recommended_action"]


def test_rapid_alerts_ignore_out_of_order_timestamps():
    engine = AlertEscalationEngine("TEST-KEY")
    engine.evaluate_score(10, "2026-01-05T00:00:00")
    alerts = engine.evaluate_score(30, "2026-01-01T00:00:00")
    assert all(alert.category != "rapid_change" for alert in alerts)


def test_longitudinal_requires_distinct_timestamps():
    tracker = LongitudinalTracker("TEST-KEY")
    tracker.add_entry(17, 12, 10, timestamp="2026-01-01T00:00:00")
    tracker.add_entry(18, 12, 10, timestamp="2026-01-01T00:00:00")
    assert tracker.compute_trend().trend_direction == "insufficient_data"


def test_longitudinal_not_sole_indicator_of_steroid_response():
    tracker = LongitudinalTracker("TEST-KEY")
    tracker.add_entry(20, 12, 10, timestamp="2026-01-01T00:00:00")
    tracker.add_entry(17, 12, 10, timestamp="2026-01-05T00:00:00")
    analysis = tracker.correlate_with_outcomes({"steroid_response": True})
    assert "not_determinable" in analysis["steroid_response"]


def test_longitudinal_csv_missing_clinical_column(tmp_path):
    path = tmp_path / "scores.csv"
    path.write_text("pt_seconds,bilirubin_mg_dl\\n17,10\\n", encoding="utf-8")
    with pytest.raises(ValueError, match="control_pt_seconds"):
        load_from_csv(str(path), "TEST-KEY")
