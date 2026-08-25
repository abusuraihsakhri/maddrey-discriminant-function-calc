#!/usr/bin/env python3
"""
EHR/FHIR Integration for Maddrey Discriminant Function (mDF).
Auto-populates scoring components from FHIR Observation and Condition resources,
supports CDS Hooks integration for real-time scoring at point of care.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional


# FHIR resource type constants
FHIR_OBSERVATION = "Observation"
FHIR_CONDITION = "Condition"
FHIR_DIAGNOSTIC_REPORT = "DiagnosticReport"

# LOINC codes for mDF components
LOINC_PT = "5902-2"           # Prothrombin time (PT)
LOINC_CONTROL_PT = "5960-0"   # PT control
LOINC_BILIRUBIN = "1975-2"    # Bilirubin [Mass/volume] in Serum or Plasma


def extract_fhir_observation(resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract relevant data from a FHIR Observation resource."""
    if resource.get("resourceType") != FHIR_OBSERVATION:
        return None

    code = resource.get("code", {})
    coding = code.get("coding", [{}])
    loinc_code = coding[0].get("code", "") if coding else ""

    value_quantity = resource.get("valueQuantity", {})
    value = value_quantity.get("value")
    unit = value_quantity.get("unit", "")

    effective_dt = resource.get("effectiveDateTime", "")

    return {
        "loinc_code": loinc_code,
        "display": coding[0].get("display", "") if coding else "",
        "value": value,
        "unit": unit,
        "effective_datetime": effective_dt,
        "subject": resource.get("subject", {}).get("reference", ""),
    }


def extract_mdf_components(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract mDF components from a list of FHIR Observations."""
    pt_value = None
    control_pt_value = None
    bilirubin_value = None
    effective_date = None

    for obs_resource in observations:
        extracted = extract_fhir_observation(obs_resource)
        if not extracted:
            continue

        code = extracted["loinc_code"]
        val = extracted["value"]

        if code == LOINC_PT and val is not None:
            pt_value = float(val)
            effective_date = extracted["effective_datetime"]
        elif code == LOINC_CONTROL_PT and val is not None:
            control_pt_value = float(val)
        elif code == LOINC_BILIRUBIN and val is not None:
            bilirubin_value = float(val)

    return {
        "pt_seconds": pt_value,
        "control_pt_seconds": control_pt_value,
        "bilirubin_mg_dl": bilirubin_value,
        "effective_date": effective_date,
        "complete": all(v is not None for v in [pt_value, control_pt_value, bilirubin_value]),
    }


def build_fhir_observation_response(loinc_code: str, display: str,
                                      value: float, unit: str,
                                      patient_ref: str) -> Dict[str, Any]:
    """Build a FHIR Observation resource for an mDF component."""
    return {
        "resourceType": FHIR_OBSERVATION,
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "Laboratory",
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": loinc_code,
                "display": display,
            }]
        },
        "subject": {"reference": patient_ref},
        "effectiveDateTime": datetime.now().isoformat(),
        "valueQuantity": {
            "value": value,
            "unit": unit,
            "system": "http://unitsofmeasure.org",
        },
    }


def build_mdf_diagnostic_report(mdf_score: float, classification: str,
                                  patient_ref: str,
                                  component_refs: List[str]) -> Dict[str, Any]:
    """Build a FHIR DiagnosticReport for the computed mDF score."""
    return {
        "resourceType": FHIR_DIAGNOSTIC_REPORT,
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": "LAB",
                "display": "Laboratory",
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "76498-9",
                "display": "Maddrey Discriminant Function",
            }],
            "text": "Maddrey Discriminant Function (mDF)",
        },
        "subject": {"reference": patient_ref},
        "effectiveDateTime": datetime.now().isoformat(),
        "conclusion": f"mDF = {mdf_score:.1f} — {classification}",
        "result": [{"reference": ref} for ref in component_refs],
    }


def build_cds_hooks_request(patient_id: str, observations: List[Dict[str, Any]],
                              encounter_id: Optional[str] = None) -> Dict[str, Any]:
    """Build a CDS Hooks request for mDF computation at point of care."""
    hook_request = {
        "hook": "patient-view",
        "hookInstance": f"maddrey-df-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "context": {
            "patientId": patient_id,
        },
        "prefetch": {
            "ptObservation": {
                "resourceType": "Bundle",
                "type": "collection",
                "entry": [{"resource": obs} for obs in observations],
            }
        },
    }
    if encounter_id:
        hook_request["context"]["encounterId"] = encounter_id
    return hook_request


def build_cds_hooks_card(mdf_score: float, classification: str,
                           patient_id: str) -> Dict[str, Any]:
    """Build a CDS Hooks response card for mDF result."""
    if mdf_score >= 32:
        indicator = "critical"
        summary = f"mDF = {mdf_score:.1f} — Consider corticosteroid therapy"
        detail = (f"Maddrey DF score of {mdf_score:.1f} is >= 32, indicating severe alcoholic hepatitis. "
                  f"Corticosteroid therapy (prednisolone 40mg/day x 28 days) is recommended per AASLD guidelines.")
    elif mdf_score >= 20:
        indicator = "warning"
        summary = f"mDF = {mdf_score:.1f} — Monitor closely"
        detail = (f"Maddrey DF score of {mdf_score:.1f} is in the intermediate range. "
                  f"Consider clinical context and additional scoring (MELD, Lille) before treatment decisions.")
    else:
        indicator = "info"
        summary = f"mDF = {mdf_score:.1f} — Low severity"
        detail = f"Maddrey DF score of {mdf_score:.1f} is below 32. Corticosteroid therapy is not indicated."

    return {
        "cards": [{
            "summary": summary,
            "indicator": indicator,
            "detail": detail,
            "source": {
                "label": "Maddrey DF Calculator",
                "type": "system",
            },
            "links": [{
                "label": "View mDF Trend",
                "url": f"/api/patients/{patient_id}/mdf-trend",
                "type": "absolute",
            }],
        }]
    }


class FHIRmDFIntegration:
    """High-level FHIR integration for Maddrey DF computation."""

    def __init__(self, patient_ref: str):
        self.patient_ref = patient_ref
        self.observations: List[Dict[str, Any]] = []

    def ingest_observation(self, resource: Dict[str, Any]) -> bool:
        """Ingest a FHIR Observation resource. Returns True if relevant to mDF."""
        extracted = extract_fhir_observation(resource)
        if extracted and extracted["loinc_code"] in [LOINC_PT, LOINC_CONTROL_PT, LOINC_BILIRUBIN]:
            self.observations.append(resource)
            return True
        return False

    def ingest_bundle(self, bundle: Dict[str, Any]) -> int:
        """Ingest a FHIR Bundle. Returns count of relevant observations found."""
        count = 0
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if self.ingest_observation(resource):
                count += 1
        return count

    def compute_from_fhir(self) -> Dict[str, Any]:
        """Compute mDF from ingested FHIR observations."""
        components = extract_mdf_components(self.observations)

        if not components["complete"]:
            missing = []
            if components["pt_seconds"] is None:
                missing.append("PT (LOINC 5902-2)")
            if components["control_pt_seconds"] is None:
                missing.append("Control PT (LOINC 5960-0)")
            if components["bilirubin_mg_dl"] is None:
                missing.append("Bilirubin (LOINC 1975-2)")
            return {
                "status": "incomplete",
                "missing_components": missing,
                "available": {k: v for k, v in components.items() if v is not None and k != "complete"},
            }

        mdf = 4.6 * (components["pt_seconds"] - components["control_pt_seconds"]) + components["bilirubin_mg_dl"]

        if mdf < 32:
            classification = "Low severity - No corticosteroid benefit"
        elif mdf <= 54:
            classification = "Moderate-Severe - Consider corticosteroids"
        else:
            classification = "Severe - Strong corticosteroid indication"

        report = build_mdf_diagnostic_report(
            mdf_score=mdf,
            classification=classification,
            patient_ref=self.patient_ref,
            component_refs=[f"Observation/pt-{self.patient_ref}",
                           f"Observation/control-pt-{self.patient_ref}",
                           f"Observation/bilirubin-{self.patient_ref}"],
        )

        return {
            "status": "complete",
            "mdf_score": round(mdf, 2),
            "classification": classification,
            "components": components,
            "fhir_diagnostic_report": report,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FHIR Integration for Maddrey DF")
    parser.add_argument("--input", required=True, help="FHIR Bundle JSON file")
    parser.add_argument("--patient-ref", default="Patient/example", help="FHIR patient reference")
    parser.add_argument("--output", default="fhir_mdf_result.json", help="Output JSON")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        bundle = json.load(f)

    integration = FHIRmDFIntegration(args.patient_ref)
    integration.ingest_bundle(bundle)
    result = integration.compute_from_fhir()

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
