import math
import pytest
from fhir_integration import (
    FHIRmDFIntegration, extract_mdf_components, LOINC_PT, LOINC_BILIRUBIN
)


def observation(code, value, unit):
    return {
        "resourceType": "Observation",
        "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
        "valueQuantity": {"value": value, "code": unit},
    }


def test_fhir_requires_explicit_laboratory_control_pt():
    records = [observation(LOINC_PT, 17, "s"), observation(LOINC_BILIRUBIN, 10, "mg/dL")]
    integration = FHIRmDFIntegration("Patient/example")
    assert integration.ingest_observation(records[0])
    assert integration.ingest_observation(records[1])
    assert integration.compute_from_fhir()["status"] == "incomplete"

    known_control = FHIRmDFIntegration("Patient/example", control_pt_seconds=12)
    known_control.ingest_bundle({"entry": [{"resource": obs} for obs in records]})
    result = known_control.compute_from_fhir()
    assert result["mdf_score"] == 33
    assert result["status"] == "complete"


def test_fhir_bilirubin_umol_conversion():
    components = extract_mdf_components(
        [observation(LOINC_PT, 17, "s"), observation(LOINC_BILIRUBIN, 171.04, "umol/L")],
        control_pt_seconds=12,
    )
    assert math.isclose(components["bilirubin_mg_dl"], 10, rel_tol=1e-4)


def test_deprecated_control_loinc_does_not_set_control():
    components = extract_mdf_components(
        [observation("5960-0", 12, "s"), observation(LOINC_PT, 17, "s"),
         observation(LOINC_BILIRUBIN, 10, "mg/dL")],
    )
    assert components["control_pt_seconds"] is None
    assert not components["complete"]


def test_fhir_rejects_unrecognized_units():
    with pytest.raises(ValueError, match="Bilirubin units"):
        extract_mdf_components([observation(LOINC_BILIRUBIN, 100, "g/L")])
