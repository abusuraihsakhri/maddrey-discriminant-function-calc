#!/usr/bin/env python3
"""
Tests for Maddrey Discriminant Function, ABIC, MELD, and Steroid Eligibility.
"""
import json
import math
import sys
import os
import csv
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from maddrey_df import (
    calculate_maddrey_df,
    calculate_abic,
    calculate_meld,
    assess_steroid_eligibility,
    comprehensive_assessment,
    main,
)


# =============================================================================
# Maddrey DF Tests
# =============================================================================

class TestMaddreyDF:
    def test_mdf_mild(self):
        """mDF < 32: mild alcoholic hepatitis."""
        # PT diff = 2, bilirubin = 5 => 4.6*2 + 5 = 14.2
        result = calculate_maddrey_df(pt_patient=14.0, pt_control=12.0, bilirubin_mg_dl=5.0)
        assert result["mdf_score"] == 14.2
        assert result["severity"] == "Mild"
        assert result["steroid_eligible_by_mdf"] is False

    def test_mdf_severe(self):
        """mDF >= 32: severe alcoholic hepatitis."""
        # PT diff = 5, bilirubin = 10 => 4.6*5 + 10 = 33.0
        result = calculate_maddrey_df(pt_patient=17.0, pt_control=12.0, bilirubin_mg_dl=10.0)
        assert result["mdf_score"] == 33.0
        assert result["severity"] == "Severe"
        assert result["steroid_eligible_by_mdf"] is True

    def test_mdf_boundary_32(self):
        """mDF exactly 32 is severe."""
        # 4.6 * (PT diff) + bilirubin = 32
        # 4.6 * 5 + 9 = 32
        result = calculate_maddrey_df(pt_patient=17.0, pt_control=12.0, bilirubin_mg_dl=9.0)
        assert result["mdf_score"] == 32.0
        assert result["severity"] == "Severe"

    def test_mdf_below_32(self):
        """mDF just below 32 is mild."""
        # 4.6 * 4 + 13.5 = 31.9
        result = calculate_maddrey_df(pt_patient=16.0, pt_control=12.0, bilirubin_mg_dl=13.5)
        assert result["mdf_score"] == 31.9
        assert result["severity"] == "Mild"

    def test_mdf_formula_accuracy(self):
        """Verify exact formula: 4.6 * (PT_patient - PT_control) + bilirubin."""
        result = calculate_maddrey_df(pt_patient=20.0, pt_control=12.0, bilirubin_mg_dl=15.0)
        expected = 4.6 * (20.0 - 12.0) + 15.0  # 36.8 + 15 = 51.8
        assert result["mdf_score"] == expected

    def test_mdf_zero_pt_difference(self):
        """Zero PT difference means mDF = bilirubin."""
        result = calculate_maddrey_df(pt_patient=12.0, pt_control=12.0, bilirubin_mg_dl=10.0)
        assert result["mdf_score"] == 10.0

    def test_mdf_components(self):
        """Verify component breakdown."""
        result = calculate_maddrey_df(pt_patient=18.0, pt_control=12.0, bilirubin_mg_dl=12.0)
        assert result["components"]["pt_patient"] == 18.0
        assert result["components"]["pt_control"] == 12.0
        assert result["components"]["pt_difference"] == 6.0
        assert result["components"]["bilirubin_mg_dl"] == 12.0


# =============================================================================
# ABIC Score Tests
# =============================================================================

class TestABIC:
    def test_abic_low_risk(self):
        """Low-risk ABIC score."""
        result = calculate_abic(age=40, bilirubin_mg_dl=5.0, inr=1.2, creatinine_mg_dl=0.8)
        expected = round(40*0.1 + 5.0*0.08 + 1.2*0.1 + 0.8*0.3, 2)  # 4.76
        assert abs(result["abic_score"] - expected) < 0.01
        assert result["risk_group"] == "Low"
        assert result["estimated_1y_survival_percent"] == 100.0

    def test_abic_intermediate_risk(self):
        """Intermediate-risk ABIC score."""
        result = calculate_abic(age=55, bilirubin_mg_dl=15.0, inr=2.0, creatinine_mg_dl=1.5)
        expected = round(55*0.1 + 15.0*0.08 + 2.0*0.1 + 1.5*0.3, 2)  # 7.35
        assert abs(result["abic_score"] - expected) < 0.01
        assert result["risk_group"] == "Intermediate"
        assert result["estimated_1y_survival_percent"] == 70.0

    def test_abic_high_risk(self):
        """High-risk ABIC score."""
        result = calculate_abic(age=65, bilirubin_mg_dl=25.0, inr=3.0, creatinine_mg_dl=3.0)
        expected = round(65*0.1 + 25.0*0.08 + 3.0*0.1 + 3.0*0.3, 2)  # 9.7
        assert abs(result["abic_score"] - expected) < 0.01
        assert result["risk_group"] == "High"
        assert result["estimated_1y_survival_percent"] == 25.0

    def test_abic_boundary_low(self):
        """ABIC exactly 6.71 is intermediate."""
        # Need: age*0.1 + bili*0.08 + inr*0.1 + crea*0.3 = 6.71
        result = calculate_abic(age=50, bilirubin_mg_dl=10.0, inr=1.5, creatinine_mg_dl=1.0)
        expected = 50*0.1 + 10.0*0.08 + 1.5*0.1 + 1.0*0.3  # 5.0 + 0.8 + 0.15 + 0.3 = 6.25
        assert result["abic_score"] == expected
        assert result["risk_group"] == "Low"

    def test_abic_boundary_high(self):
        """ABIC >= 9.0 is high risk."""
        result = calculate_abic(age=70, bilirubin_mg_dl=20.0, inr=2.5, creatinine_mg_dl=2.0)
        expected = 70*0.1 + 20.0*0.08 + 2.5*0.1 + 2.0*0.3  # 7.0 + 1.6 + 0.25 + 0.6 = 9.45
        assert result["abic_score"] == expected
        assert result["risk_group"] == "High"


# =============================================================================
# MELD Score Tests
# =============================================================================

class TestMELD:
    def test_meld_low(self):
        """Low MELD score with minimal values (all clamped to 1.0)."""
        # With clamping: 3.78*ln(1) + 11.2*ln(1) + 9.57*ln(1) + 6.43 = 6.43
        result = calculate_meld(bilirubin_mg_dl=1.0, inr=1.0, creatinine_mg_dl=1.0)
        assert result["meld_score"] == 6.4
        assert result["mortality_risk"] == "Low"

    def test_meld_moderate(self):
        """Moderate MELD score."""
        # bilirubin=2.0, inr=1.2, creatinine=1.0 => MELD ~11.1
        result = calculate_meld(bilirubin_mg_dl=2.0, inr=1.2, creatinine_mg_dl=1.0)
        assert 10 <= result["meld_score"] < 15
        assert result["mortality_risk"] == "Moderate"

    def test_meld_high(self):
        """High MELD score."""
        result = calculate_meld(bilirubin_mg_dl=15.0, inr=3.0, creatinine_mg_dl=3.0)
        assert result["meld_score"] >= 20

    def test_meld_minimum_values(self):
        """MELD clamps minimum bilirubin, INR, creatinine to 1.0."""
        result = calculate_meld(bilirubin_mg_dl=0.5, inr=0.8, creatinine_mg_dl=0.5)
        # With clamping: 3.78*ln(1) + 11.2*ln(1) + 9.57*ln(1) + 6.43 = 6.43
        assert result["meld_score"] == 6.4

    def test_meld_capped_creatinine(self):
        """MELD caps creatinine at 4.0."""
        result1 = calculate_meld(bilirubin_mg_dl=5.0, inr=2.0, creatinine_mg_dl=4.0)
        result2 = calculate_meld(bilirubin_mg_dl=5.0, inr=2.0, creatinine_mg_dl=8.0)
        assert result1["meld_score"] == result2["meld_score"]

    def test_meld_formula_accuracy(self):
        """Verify exact MELD formula."""
        bili, inr_val, crea = 3.0, 1.5, 1.2
        expected = 3.78 * math.log(bili) + 11.2 * math.log(inr_val) + 9.57 * math.log(crea) + 6.43
        result = calculate_meld(bilirubin_mg_dl=bili, inr=inr_val, creatinine_mg_dl=crea)
        assert abs(result["meld_score"] - round(expected, 1)) < 0.1


# =============================================================================
# Steroid Eligibility Tests
# =============================================================================

class TestSteroidEligibility:
    def test_eligible_severe_no_contraindications(self):
        """Severe AH with no contraindications: eligible."""
        result = assess_steroid_eligibility(mdf_score=40.0)
        assert result["eligible"] is True
        assert result["severe_hepatitis"] is True
        assert len(result["contraindications"]) == 0

    def test_not_eligible_mild(self):
        """mDF < 32: not eligible (not indicated)."""
        result = assess_steroid_eligibility(mdf_score=20.0)
        assert result["eligible"] is False
        assert result["severe_hepatitis"] is False

    def test_not_eligible_infection(self):
        """Active infection is a contraindication."""
        result = assess_steroid_eligibility(mdf_score=40.0, active_infection=True)
        assert result["eligible"] is False
        assert "Active infection" in result["contraindications"]

    def test_not_eligible_gi_bleeding(self):
        """GI bleeding is a contraindication."""
        result = assess_steroid_eligibility(mdf_score=40.0, gi_bleeding=True)
        assert result["eligible"] is False
        assert "Active GI bleeding" in result["contraindications"]

    def test_not_eligible_pancreatitis(self):
        """Acute pancreatitis is a contraindication."""
        result = assess_steroid_eligibility(mdf_score=40.0, acute_pancreatitis=True)
        assert result["eligible"] is False
        assert "Acute pancreatitis" in result["contraindications"]

    def test_not_eligible_hepatorenal(self):
        """Hepatorenal syndrome is a contraindication."""
        result = assess_steroid_eligibility(mdf_score=40.0, hepatorenal_syndrome=True)
        assert result["eligible"] is False
        assert "Hepatorenal syndrome" in result["contraindications"]

    def test_multiple_contraindications(self):
        """Multiple contraindications all listed."""
        result = assess_steroid_eligibility(
            mdf_score=40.0,
            active_infection=True,
            gi_bleeding=True,
        )
        assert result["eligible"] is False
        assert len(result["contraindications"]) == 2


# =============================================================================
# Comprehensive Assessment Tests
# =============================================================================

class TestComprehensive:
    def test_comprehensive_has_all_scores(self):
        """Comprehensive assessment includes all scoring systems."""
        result = comprehensive_assessment(
            pt_patient=18.0, pt_control=12.0,
            bilirubin_mg_dl=15.0, age=55,
            inr=2.0, creatinine_mg_dl=1.5,
        )
        assert "maddrey_df" in result
        assert "abic" in result
        assert "meld" in result
        assert "steroid_eligibility" in result

    def test_comprehensive_mild_case(self):
        """Mild case: low mDF, not steroid eligible."""
        result = comprehensive_assessment(
            pt_patient=13.0, pt_control=12.0,
            bilirubin_mg_dl=5.0, age=40,
            inr=1.2, creatinine_mg_dl=0.8,
        )
        assert result["maddrey_df"]["severity"] == "Mild"
        assert result["steroid_eligibility"]["eligible"] is False

    def test_comprehensive_severe_eligible(self):
        """Severe case with no contraindications: eligible for steroids."""
        result = comprehensive_assessment(
            pt_patient=20.0, pt_control=12.0,
            bilirubin_mg_dl=20.0, age=55,
            inr=2.5, creatinine_mg_dl=1.2,
        )
        assert result["maddrey_df"]["severity"] == "Severe"
        assert result["steroid_eligibility"]["eligible"] is True


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    def test_cli_mdf(self):
        ret = main(["mdf", "--pt-patient", "17.0", "--pt-control", "12.0",
                     "--bilirubin", "10.0"])
        assert ret == 0

    def test_cli_abic(self):
        ret = main(["abic", "--age", "55", "--bilirubin", "15.0",
                     "--inr", "2.0", "--creatinine", "1.5"])
        assert ret == 0

    def test_cli_meld(self):
        ret = main(["meld", "--bilirubin", "5.0", "--inr", "2.0",
                     "--creatinine", "1.5"])
        assert ret == 0

    def test_cli_steroid(self):
        ret = main(["steroid", "--mdf", "40.0"])
        assert ret == 0

    def test_cli_comprehensive(self):
        ret = main(["comprehensive", "--pt-patient", "18.0", "--pt-control", "12.0",
                     "--bilirubin", "15.0", "--age", "55", "--inr", "2.0",
                     "--creatinine", "1.5"])
        assert ret == 0

    def test_cli_batch(self, tmp_path):
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "pt_patient,pt_control,bilirubin\n17.0,12.0,10.0\n",
            encoding="utf-8",
        )
        ret = main(["batch", "-i", str(csv_in), "-o", str(csv_out), "--score", "mdf"])
        assert ret == 0
        assert csv_out.exists()


# =============================================================================
# Input Validation Tests
# =============================================================================

class TestInputValidation:
    def test_mdf_rejects_negative_bilirubin(self):
        with pytest.raises(ValueError, match="bilirubin_mg_dl"):
            calculate_maddrey_df(pt_patient=15.0, pt_control=12.0, bilirubin_mg_dl=-1.0)

    def test_mdf_rejects_nan(self):
        with pytest.raises(ValueError, match="finite"):
            calculate_maddrey_df(pt_patient=float("nan"), pt_control=12.0, bilirubin_mg_dl=5.0)

    def test_mdf_rejects_inf(self):
        with pytest.raises(ValueError, match="finite"):
            calculate_maddrey_df(pt_patient=float("inf"), pt_control=12.0, bilirubin_mg_dl=5.0)

    def test_mdf_rejects_extreme_pt(self):
        with pytest.raises(ValueError, match="pt_patient"):
            calculate_maddrey_df(pt_patient=200.0, pt_control=12.0, bilirubin_mg_dl=5.0)

    def test_abic_rejects_negative_age(self):
        with pytest.raises(ValueError, match="age"):
            calculate_abic(age=-5, bilirubin_mg_dl=5.0, inr=1.2, creatinine_mg_dl=1.0)

    def test_abic_rejects_extreme_inr(self):
        with pytest.raises(ValueError, match="inr"):
            calculate_abic(age=50, bilirubin_mg_dl=5.0, inr=50.0, creatinine_mg_dl=1.0)

    def test_meld_rejects_negative_bilirubin(self):
        with pytest.raises(ValueError, match="bilirubin_mg_dl"):
            calculate_meld(bilirubin_mg_dl=-0.5, inr=1.2, creatinine_mg_dl=1.0)

    def test_meld_rejects_negative_creatinine(self):
        with pytest.raises(ValueError, match="creatinine_mg_dl"):
            calculate_meld(bilirubin_mg_dl=5.0, inr=1.2, creatinine_mg_dl=-1.0)

    def test_steroid_rejects_negative_mdf(self):
        with pytest.raises(ValueError, match="mdf_score"):
            assess_steroid_eligibility(mdf_score=-5.0)

    def test_valid_inputs_accepted(self):
        """Normal clinical values should not raise."""
        result = calculate_maddrey_df(pt_patient=15.0, pt_control=12.0, bilirubin_mg_dl=5.0)
        assert result["mdf_score"] > 0


# =============================================================================
# New CLI Subcommand Tests
# =============================================================================

class TestNewCLICommands:
    def test_cli_audit(self):
        ret = main(["audit", "--task-id", "TEST-AUDIT-01"])
        assert ret == 0

    def test_cli_chat(self):
        ret = main(["chat", "Explain", "mDF"])
        assert ret == 0

    def test_cli_verify_audit(self):
        ret = main(["verify-audit"])
        assert ret == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
