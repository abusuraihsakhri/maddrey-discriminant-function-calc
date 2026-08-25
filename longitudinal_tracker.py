#!/usr/bin/env python3
"""
Longitudinal Score Tracking for Maddrey Discriminant Function (mDF).
Stores sequential mDF assessments with date-stamped clinical parameters,
tracks score trajectory with treatment interventions, and classifies trends.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import json
import csv
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class ScoreEntry:
    """A single Maddrey DF score assessment."""
    timestamp: str
    pt_seconds: float
    bilirubin_mg_dl: float
    control_pt_seconds: float
    mdf_score: float
    classification: str
    treatment: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class TrendResult:
    """Result of trend analysis over longitudinal scores."""
    trend_direction: str  # improving | stable | deteriorating
    slope_per_day: float
    r_squared: float
    days_tracked: int
    score_change: float
    clinical_significance: str


@dataclass
class LongitudinalReport:
    """Complete longitudinal tracking report."""
    patient_id: str
    entries: List[ScoreEntry]
    trend: TrendResult
    outcome_correlation: Dict[str, Any]
    alerts: List[str]


def calculate_mdf(pt_seconds: float, control_pt_seconds: float, bilirubin_mg_dl: float) -> float:
    """Calculate Maddrey's Discriminant Function.
    mDF = 4.6 × (PT_patient - PT_control) + Bilirubin
    """
    return 4.6 * (pt_seconds - control_pt_seconds) + bilirubin_mg_dl


def classify_mdf(mdf: float) -> str:
    """Classify mDF score into clinical tiers."""
    if mdf < 32:
        return "Low (mDF < 32) - No corticosteroid benefit"
    elif mdf <= 54:
        return "Moderate-Severe (32-54) - Consider corticosteroids"
    else:
        return "Severe (mDF > 54) - Strong corticosteroid indication"


class LongitudinalTracker:
    """Tracks Maddrey DF scores over time for a patient."""

    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.entries: List[ScoreEntry] = []

    def add_entry(self, pt_seconds: float, control_pt_seconds: float,
                  bilirubin_mg_dl: float, treatment: Optional[str] = None,
                  notes: Optional[str] = None,
                  timestamp: Optional[str] = None) -> ScoreEntry:
        """Add a new score assessment."""
        ts = timestamp or datetime.now().isoformat()
        mdf = calculate_mdf(pt_seconds, control_pt_seconds, bilirubin_mg_dl)
        entry = ScoreEntry(
            timestamp=ts,
            pt_seconds=pt_seconds,
            bilirubin_mg_dl=bilirubin_mg_dl,
            control_pt_seconds=control_pt_seconds,
            mdf_score=round(mdf, 2),
            classification=classify_mdf(mdf),
            treatment=treatment,
            notes=notes,
        )
        self.entries.append(entry)
        return entry

    def compute_trend(self) -> TrendResult:
        """Analyze score trajectory using linear regression."""
        if len(self.entries) < 2:
            return TrendResult(
                trend_direction="insufficient_data",
                slope_per_day=0.0,
                r_squared=0.0,
                days_tracked=0,
                score_change=0.0,
                clinical_significance="Need at least 2 assessments for trend analysis",
            )

        # Parse timestamps and compute days from first entry
        timestamps = [datetime.fromisoformat(e.timestamp) for e in self.entries]
        days = [(t - timestamps[0]).total_seconds() / 86400.0 for t in timestamps]
        scores = [e.mdf_score for e in self.entries]

        n = len(scores)
        sum_x = sum(days)
        sum_y = sum(scores)
        sum_xy = sum(d * s for d, s in zip(days, scores))
        sum_x2 = sum(d * d for d in days)
        sum_y2 = sum(s * s for s in scores)

        denom = n * sum_x2 - sum_x * sum_x
        if denom == 0:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denom

        # R-squared
        mean_y = sum_y / n
        ss_tot = sum((s - mean_y) ** 2 for s in scores)
        intercept = (sum_y - slope * sum_x) / n
        ss_res = sum((s - (intercept + slope * d)) ** 2 for s, d in zip(scores, days))
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        score_change = scores[-1] - scores[0]
        days_tracked = days[-1] - days[0]

        # Classify trend
        if slope < -0.5:
            direction = "improving"
            significance = "mDF declining - treatment may be effective"
        elif slope > 0.5:
            direction = "deteriorating"
            significance = "mDF rising - consider treatment escalation or alternative therapy"
        else:
            direction = "stable"
            significance = "mDF stable - continue current management"

        return TrendResult(
            trend_direction=direction,
            slope_per_day=round(slope, 4),
            r_squared=round(r_squared, 4),
            days_tracked=round(days_tracked, 1),
            score_change=round(score_change, 2),
            clinical_significance=significance,
        )

    def correlate_with_outcomes(self, outcomes: Dict[str, Any]) -> Dict[str, Any]:
        """Correlate score changes with clinical outcomes."""
        trend = self.compute_trend()
        latest = self.entries[-1] if self.entries else None

        correlation = {
            "patient_id": self.patient_id,
            "latest_mdf": latest.mdf_score if latest else None,
            "trend": trend.trend_direction,
            "slope": trend.slope_per_day,
        }

        if outcomes.get("mortality"):
            correlation["mortality_risk"] = "high" if latest and latest.mdf_score >= 32 else "low"
        if outcomes.get("steroid_response"):
            if trend.trend_direction == "improving":
                correlation["steroid_response"] = "likely_responder"
            elif trend.trend_direction == "deteriorating":
                correlation["steroid_response"] = "likely_non_responder"
            else:
                correlation["steroid_response"] = "indeterminate"

        return correlation

    def generate_report(self, outcomes: Optional[Dict[str, Any]] = None) -> LongitudinalReport:
        """Generate a complete longitudinal report."""
        trend = self.compute_trend()
        alerts = []

        if self.entries:
            latest = self.entries[-1]
            if latest.mdf_score >= 32:
                alerts.append(f"CRITICAL: Latest mDF = {latest.mdf_score} >= 32. Consider corticosteroid therapy.")
            if trend.trend_direction == "deteriorating":
                alerts.append(f"WARNING: mDF trending upward (slope={trend.slope_per_day}/day). Reassess treatment.")

        outcome_corr = self.correlate_with_outcomes(outcomes or {})

        return LongitudinalReport(
            patient_id=self.patient_id,
            entries=self.entries,
            trend=trend,
            outcome_correlation=outcome_corr,
            alerts=alerts,
        )

    def export_csv(self, output_path: str) -> None:
        """Export longitudinal data to CSV."""
        fieldnames = ["timestamp", "pt_seconds", "control_pt_seconds", "bilirubin_mg_dl",
                       "mdf_score", "classification", "treatment", "notes"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in self.entries:
                writer.writerow(asdict(e))

    def export_json(self, output_path: str) -> None:
        """Export longitudinal report to JSON."""
        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)


def load_from_csv(input_csv: str, patient_id: str) -> LongitudinalTracker:
    """Load longitudinal data from a CSV file."""
    tracker = LongitudinalTracker(patient_id)
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tracker.add_entry(
                pt_seconds=float(row.get("pt_seconds", 0)),
                control_pt_seconds=float(row.get("control_pt_seconds", 12.0)),
                bilirubin_mg_dl=float(row.get("bilirubin_mg_dl", 0)),
                treatment=row.get("treatment"),
                notes=row.get("notes"),
                timestamp=row.get("timestamp"),
            )
    return tracker


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Maddrey DF Longitudinal Tracker")
    parser.add_argument("--input", required=True, help="Input CSV with serial assessments")
    parser.add_argument("--patient-id", default="PATIENT-001", help="Patient identifier")
    parser.add_argument("--output", default="longitudinal_report.json", help="Output report path")
    args = parser.parse_args()

    tracker = load_from_csv(args.input, args.patient_id)
    report = tracker.generate_report()
    tracker.export_json(args.output)
    print(json.dumps(asdict(report), indent=2, default=str))
