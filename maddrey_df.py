#!/usr/bin/env python3
"""
Maddrey Discriminant Function (mDF) for Alcoholic Hepatitis
Calculates mDF, ABIC score, and MELD score with steroid eligibility assessment.

mDF = 4.6 * (PT_patient - PT_control) + bilirubin_mg_dL
  - <32: Mild alcoholic hepatitis (supportive care)
  - >=32: Severe alcoholic hepatitis (consider corticosteroids)

ABIC = (Age * 0.1) + (Bilirubin * 0.08) + (INR * 0.1) + (Creatinine * 0.3)
  - <6.71: Low mortality risk (1-year survival ~100%)
  - 6.71-8.99: Intermediate risk (1-year survival ~70%)
  - >=9.0: High risk (1-year survival ~25%)

MELD = 3.78 * ln(Bilirubin) + 11.2 * ln(INR) + 9.57 * ln(Creatinine) + 6.43

References:
  - Maddrey WC, et al. Hepatology 1989;9:675-80.
  - Dominguez M, et al. Gastroenterology 2008;135:865-73 (ABIC).
  - Kamath PS, et al. Hepatology 2001;33:464-70 (MELD).

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import sys
from typing import Dict, Any, List, Optional


def calculate_maddrey_df(
    pt_patient: float,
    pt_control: float,
    bilirubin_mg_dl: float,
) -> Dict[str, Any]:
    """
    Calculate Maddrey Discriminant Function.

    Parameters:
        pt_patient: Patient's prothrombin time in seconds
        pt_control: Control (normal) prothrombin time in seconds
        bilirubin_mg_dl: Serum bilirubin in mg/dL

    Returns:
        Dict with mDF score, severity classification, and recommendation.
    """
    mdf = 4.6 * (pt_patient - pt_control) + bilirubin_mg_dl
    mdf = round(mdf, 2)

    if mdf < 32:
        severity = "Mild"
        recommendation = "Mild alcoholic hepatitis. Supportive care recommended. Corticosteroids not indicated."
        steroid_eligible = False
    else:
        severity = "Severe"
        recommendation = "Severe alcoholic hepatitis. Consider corticosteroids (prednisolone 40 mg/day for 28 days) if no contraindications."
        steroid_eligible = True

    return {
        "tool": "maddrey-discriminant-function",
        "mdf_score": mdf,
        "severity": severity,
        "steroid_eligible_by_mdf": steroid_eligible,
        "recommendation": recommendation,
        "components": {
            "pt_patient": pt_patient,
            "pt_control": pt_control,
            "pt_difference": round(pt_patient - pt_control, 2),
            "bilirubin_mg_dl": bilirubin_mg_dl,
        },
    }


def calculate_abic(
    age: int,
    bilirubin_mg_dl: float,
    inr: float,
    creatinine_mg_dl: float,
) -> Dict[str, Any]:
    """
    Calculate ABIC (Age, Bilirubin, INR, Creatinine) score.

    ABIC = (Age * 0.1) + (Bilirubin * 0.08) + (INR * 0.1) + (Creatinine * 0.3)

    Parameters:
        age: Patient age in years
        bilirubin_mg_dl: Serum bilirubin in mg/dL
        inr: International normalized ratio
        creatinine_mg_dl: Serum creatinine in mg/dL

    Returns:
        Dict with ABIC score, risk group, and survival estimate.
    """
    abic = (age * 0.1) + (bilirubin_mg_dl * 0.08) + (inr * 0.1) + (creatinine_mg_dl * 0.3)
    abic = round(abic, 2)

    if abic < 6.71:
        risk_group = "Low"
        survival_1y = 100.0
        recommendation = "Low mortality risk. Supportive care with monitoring."
    elif abic <= 8.99:
        risk_group = "Intermediate"
        survival_1y = 70.0
        recommendation = "Intermediate mortality risk. Consider corticosteroids. Close monitoring required."
    else:
        risk_group = "High"
        survival_1y = 25.0
        recommendation = "High mortality risk. Consider corticosteroids or early transplant evaluation."

    return {
        "tool": "abic-score",
        "abic_score": abic,
        "risk_group": risk_group,
        "estimated_1y_survival_percent": survival_1y,
        "recommendation": recommendation,
        "components": {
            "age": age,
            "bilirubin_mg_dl": bilirubin_mg_dl,
            "inr": inr,
            "creatinine_mg_dl": creatinine_mg_dl,
        },
    }


def calculate_meld(
    bilirubin_mg_dl: float,
    inr: float,
    creatinine_mg_dl: float,
) -> Dict[str, Any]:
    """
    Calculate MELD score for alcoholic hepatitis comparison.

    MELD = 3.78 * ln(Bilirubin) + 11.2 * ln(INR) + 9.57 * ln(Creatinine) + 6.43

    Parameters:
        bilirubin_mg_dl: Serum bilirubin in mg/dL
        inr: International normalized ratio
        creatinine_mg_dl: Serum creatinine in mg/dL

    Returns:
        Dict with MELD score and mortality risk.
    """
    # Clamp minimum values per MELD convention
    bili = max(bilirubin_mg_dl, 1.0)
    inr_val = max(inr, 1.0)
    crea = max(creatinine_mg_dl, 1.0)

    # Cap creatinine at 4.0 per MELD convention
    crea = min(crea, 4.0)

    meld = 3.78 * math.log(bili) + 11.2 * math.log(inr_val) + 9.57 * math.log(crea) + 6.43
    meld = round(meld, 1)

    if meld < 10:
        mortality_risk = "Low"
        mortality_90d = 2.0
    elif meld < 15:
        mortality_risk = "Moderate"
        mortality_90d = 6.0
    elif meld < 20:
        mortality_risk = "Moderate-High"
        mortality_90d = 10.0
    elif meld < 25:
        mortality_risk = "High"
        mortality_90d = 20.0
    elif meld < 30:
        mortality_risk = "Very High"
        mortality_90d = 35.0
    elif meld < 40:
        mortality_risk = "Critical"
        mortality_90d = 50.0
    else:
        mortality_risk = "Extreme"
        mortality_90d = 70.0

    return {
        "tool": "meld-score",
        "meld_score": meld,
        "mortality_risk": mortality_risk,
        "estimated_90d_mortality_percent": mortality_90d,
        "components": {
            "bilirubin_mg_dl": bilirubin_mg_dl,
            "inr": inr,
            "creatinine_mg_dl": creatinine_mg_dl,
        },
    }


def assess_steroid_eligibility(
    mdf_score: float,
    active_infection: bool = False,
    gi_bleeding: bool = False,
    acute_pancreatitis: bool = False,
    hepatorenal_syndrome: bool = False,
) -> Dict[str, Any]:
    """
    Assess corticosteroid eligibility for alcoholic hepatitis.

    Steroids are considered for severe AH (mDF >= 32) when no contraindications exist.

    Contraindications:
      - Active infection
      - Active GI bleeding
      - Acute pancreatitis
      - Hepatorenal syndrome

    Parameters:
        mdf_score: Maddrey Discriminant Function score
        active_infection: Presence of active infection
        gi_bleeding: Active gastrointestinal bleeding
        acute_pancreatitis: Concurrent acute pancreatitis
        hepatorenal_syndrome: Hepatorenal syndrome present

    Returns:
        Dict with eligibility assessment and contraindication details.
    """
    contraindications = []
    if active_infection:
        contraindications.append("Active infection")
    if gi_bleeding:
        contraindications.append("Active GI bleeding")
    if acute_pancreatitis:
        contraindications.append("Acute pancreatitis")
    if hepatorenal_syndrome:
        contraindications.append("Hepatorenal syndrome")

    severe = mdf_score >= 32
    has_contraindications = len(contraindications) > 0

    if not severe:
        eligible = False
        reason = "mDF < 32: Mild alcoholic hepatitis. Steroids not indicated."
    elif has_contraindications:
        eligible = False
        reason = f"mDF >= 32 but contraindications present: {', '.join(contraindications)}."
    else:
        eligible = True
        reason = "mDF >= 32 with no contraindications. Corticosteroids recommended (prednisolone 40 mg/day x 28 days)."

    return {
        "tool": "steroid-eligibility",
        "eligible": eligible,
        "mdf_score": mdf_score,
        "severe_hepatitis": severe,
        "contraindications": contraindications,
        "reason": reason,
    }


def comprehensive_assessment(
    pt_patient: float,
    pt_control: float,
    bilirubin_mg_dl: float,
    age: int,
    inr: float,
    creatinine_mg_dl: float,
    active_infection: bool = False,
    gi_bleeding: bool = False,
    acute_pancreatitis: bool = False,
    hepatorenal_syndrome: bool = False,
) -> Dict[str, Any]:
    """
    Perform comprehensive alcoholic hepatitis assessment using all scoring systems.
    """
    mdf = calculate_maddrey_df(pt_patient, pt_control, bilirubin_mg_dl)
    abic = calculate_abic(age, bilirubin_mg_dl, inr, creatinine_mg_dl)
    meld = calculate_meld(bilirubin_mg_dl, inr, creatinine_mg_dl)
    steroid = assess_steroid_eligibility(
        mdf["mdf_score"],
        active_infection=active_infection,
        gi_bleeding=gi_bleeding,
        acute_pancreatitis=acute_pancreatitis,
        hepatorenal_syndrome=hepatorenal_syndrome,
    )

    return {
        "tool": "comprehensive-ah-assessment",
        "maddrey_df": mdf,
        "abic": abic,
        "meld": meld,
        "steroid_eligibility": steroid,
    }


# =============================================================================
# CLI
# =============================================================================

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="maddrey-df",
        description="Maddrey Discriminant Function, ABIC, MELD, and Steroid Eligibility for Alcoholic Hepatitis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # mDF
    p_mdf = subparsers.add_parser("mdf", help="Calculate Maddrey Discriminant Function")
    p_mdf.add_argument("--pt-patient", type=float, required=True, help="Patient PT (seconds)")
    p_mdf.add_argument("--pt-control", type=float, required=True, help="Control PT (seconds)")
    p_mdf.add_argument("--bilirubin", type=float, required=True, help="Bilirubin (mg/dL)")

    # ABIC
    p_abic = subparsers.add_parser("abic", help="Calculate ABIC score")
    p_abic.add_argument("--age", type=int, required=True, help="Patient age")
    p_abic.add_argument("--bilirubin", type=float, required=True, help="Bilirubin (mg/dL)")
    p_abic.add_argument("--inr", type=float, required=True, help="INR")
    p_abic.add_argument("--creatinine", type=float, required=True, help="Creatinine (mg/dL)")

    # MELD
    p_meld = subparsers.add_parser("meld", help="Calculate MELD score")
    p_meld.add_argument("--bilirubin", type=float, required=True, help="Bilirubin (mg/dL)")
    p_meld.add_argument("--inr", type=float, required=True, help="INR")
    p_meld.add_argument("--creatinine", type=float, required=True, help="Creatinine (mg/dL)")

    # Steroid eligibility
    p_steroid = subparsers.add_parser("steroid", help="Assess steroid eligibility")
    p_steroid.add_argument("--mdf", type=float, required=True, help="Maddrey DF score")
    p_steroid.add_argument("--active-infection", action="store_true")
    p_steroid.add_argument("--gi-bleeding", action="store_true")
    p_steroid.add_argument("--acute-pancreatitis", action="store_true")
    p_steroid.add_argument("--hepatorenal-syndrome", action="store_true")

    # Comprehensive
    p_comp = subparsers.add_parser("comprehensive", help="Full assessment (mDF + ABIC + MELD + steroid)")
    p_comp.add_argument("--pt-patient", type=float, required=True, help="Patient PT (seconds)")
    p_comp.add_argument("--pt-control", type=float, required=True, help="Control PT (seconds)")
    p_comp.add_argument("--bilirubin", type=float, required=True, help="Bilirubin (mg/dL)")
    p_comp.add_argument("--age", type=int, required=True, help="Patient age")
    p_comp.add_argument("--inr", type=float, required=True, help="INR")
    p_comp.add_argument("--creatinine", type=float, required=True, help="Creatinine (mg/dL)")
    p_comp.add_argument("--active-infection", action="store_true")
    p_comp.add_argument("--gi-bleeding", action="store_true")
    p_comp.add_argument("--acute-pancreatitis", action="store_true")
    p_comp.add_argument("--hepatorenal-syndrome", action="store_true")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV")
    p_batch.add_argument("--score", choices=["mdf", "abic", "meld", "comprehensive"],
                         default="mdf", help="Score to calculate")

    args = parser.parse_args(argv)

    if args.command == "mdf":
        result = calculate_maddrey_df(args.pt_patient, args.pt_control, args.bilirubin)
        print(json.dumps(result, indent=2))

    elif args.command == "abic":
        result = calculate_abic(args.age, args.bilirubin, args.inr, args.creatinine)
        print(json.dumps(result, indent=2))

    elif args.command == "meld":
        result = calculate_meld(args.bilirubin, args.inr, args.creatinine)
        print(json.dumps(result, indent=2))

    elif args.command == "steroid":
        result = assess_steroid_eligibility(
            args.mdf,
            active_infection=args.active_infection,
            gi_bleeding=args.gi_bleeding,
            acute_pancreatitis=args.acute_pancreatitis,
            hepatorenal_syndrome=args.hepatorenal_syndrome,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "comprehensive":
        result = comprehensive_assessment(
            args.pt_patient, args.pt_control, args.bilirubin,
            args.age, args.inr, args.creatinine,
            active_infection=args.active_infection,
            gi_bleeding=args.gi_bleeding,
            acute_pancreatitis=args.acute_pancreatitis,
            hepatorenal_syndrome=args.hepatorenal_syndrome,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "batch":
        _run_batch(args.input, args.output, args.score)

    return 0


def _run_batch(input_csv: str, output_csv: str, score_type: str) -> None:
    """Process CSV through selected scoring system."""
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_rows = []
    for r in rows:
        if score_type == "mdf":
            result = calculate_maddrey_df(
                pt_patient=float(r.get("pt_patient", 15)),
                pt_control=float(r.get("pt_control", 12)),
                bilirubin_mg_dl=float(r.get("bilirubin", 5)),
            )
            row_dict = dict(r)
            row_dict["mdf_score"] = result["mdf_score"]
            row_dict["severity"] = result["severity"]
        elif score_type == "abic":
            result = calculate_abic(
                age=int(float(r.get("age", 50))),
                bilirubin_mg_dl=float(r.get("bilirubin", 5)),
                inr=float(r.get("inr", 1.5)),
                creatinine_mg_dl=float(r.get("creatinine", 1.0)),
            )
            row_dict = dict(r)
            row_dict["abic_score"] = result["abic_score"]
            row_dict["risk_group"] = result["risk_group"]
        elif score_type == "meld":
            result = calculate_meld(
                bilirubin_mg_dl=float(r.get("bilirubin", 5)),
                inr=float(r.get("inr", 1.5)),
                creatinine_mg_dl=float(r.get("creatinine", 1.0)),
            )
            row_dict = dict(r)
            row_dict["meld_score"] = result["meld_score"]
            row_dict["mortality_risk"] = result["mortality_risk"]
        else:
            result = comprehensive_assessment(
                pt_patient=float(r.get("pt_patient", 15)),
                pt_control=float(r.get("pt_control", 12)),
                bilirubin_mg_dl=float(r.get("bilirubin", 5)),
                age=int(float(r.get("age", 50))),
                inr=float(r.get("inr", 1.5)),
                creatinine_mg_dl=float(r.get("creatinine", 1.0)),
            )
            row_dict = dict(r)
            row_dict["mdf_score"] = result["maddrey_df"]["mdf_score"]
            row_dict["abic_score"] = result["abic"]["abic_score"]
            row_dict["meld_score"] = result["meld"]["meld_score"]
            row_dict["steroid_eligible"] = result["steroid_eligibility"]["eligible"]
        out_rows.append(row_dict)

    extra_fields = {
        "mdf": ["mdf_score", "severity"],
        "abic": ["abic_score", "risk_group"],
        "meld": ["meld_score", "mortality_risk"],
        "comprehensive": ["mdf_score", "abic_score", "meld_score", "steroid_eligible"],
    }
    out_fields = fieldnames + extra_fields.get(score_type, [])

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Processed {len(out_rows)} records -> {output_csv}")


if __name__ == "__main__":
    main()
