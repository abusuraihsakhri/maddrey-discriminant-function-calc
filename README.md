# Maddrey Discriminant Function Calculator

> **Alcoholic Hepatitis Severity Assessment and Steroid Eligibility**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)

---

## Overview

Comprehensive alcoholic hepatitis assessment implementing four validated tools:

1. **Maddrey Discriminant Function (mDF)** — Severity classification (corticosteroid threshold: 32)
2. **ABIC Score** — 1-year mortality risk stratification
3. **MELD Score** — 90-day mortality prediction
4. **Steroid Eligibility Assessment** — Contraindication screening

All formulas use Python stdlib only (no external dependencies).

---

## Scoring Systems

### Maddrey Discriminant Function (mDF)

```
mDF = 4.6 × (PT_patient - PT_control) + bilirubin_mg_dL
```

| Score | Severity | Recommendation |
|-------|----------|---------------|
| <32 | Mild | Supportive care. Steroids not indicated. |
| ≥32 | Severe | Consider corticosteroids (prednisolone 40mg/day × 28 days) |

### ABIC Score

```
ABIC = (Age × 0.1) + (Bilirubin × 0.08) + (INR × 0.1) + (Creatinine × 0.3)
```

| Score | Risk | 1-Year Survival |
|-------|------|----------------|
| <6.71 | Low | ~100% |
| 6.71-8.99 | Intermediate | ~70% |
| ≥9.0 | High | ~25% |

### MELD Score

```
MELD = 3.78 × ln(Bilirubin) + 11.2 × ln(INR) + 9.57 × ln(Creatinine) + 6.43
```

### Steroid Eligibility

Contraindications to corticosteroids:
- Active infection
- Active GI bleeding
- Acute pancreatitis
- Hepatorenal syndrome

---

## Quick Start

```bash
# Maddrey DF
python maddrey_df.py mdf --pt-patient 17.0 --pt-control 12.0 --bilirubin 10.0

# ABIC score
python maddrey_df.py abic --age 55 --bilirubin 15.0 --inr 2.0 --creatinine 1.5

# MELD score
python maddrey_df.py meld --bilirubin 5.0 --inr 2.0 --creatinine 1.5

# Steroid eligibility
python maddrey_df.py steroid --mdf 40.0 --active-infection

# Comprehensive assessment (all scores)
python maddrey_df.py comprehensive --pt-patient 18.0 --pt-control 12.0 --bilirubin 15.0 --age 55 --inr 2.0 --creatinine 1.5

# Batch processing
python maddrey_df.py batch -i patients.csv -o results.csv --score mdf
```

## Python API

```python
from maddrey_df import calculate_maddrey_df, calculate_abic, calculate_meld, assess_steroid_eligibility

# mDF
mdf = calculate_maddrey_df(pt_patient=17.0, pt_control=12.0, bilirubin_mg_dl=10.0)
print(f"mDF: {mdf['mdf_score']} ({mdf['severity']})")

# ABIC
abic = calculate_abic(age=55, bilirubin_mg_dl=15.0, inr=2.0, creatinine_mg_dl=1.5)
print(f"ABIC: {abic['abic_score']} ({abic['risk_group']})")

# MELD
meld = calculate_meld(bilirubin_mg_dl=5.0, inr=2.0, creatinine_mg_dl=1.5)
print(f"MELD: {meld['meld_score']}")

# Steroid eligibility
elig = assess_steroid_eligibility(mdf_score=40.0, active_infection=False)
print(f"Eligible: {elig['eligible']}")
```

## Tests

```bash
python -m pytest test_maddrey_df.py -v
```

## References

- Maddrey WC, et al. Corticosteroid therapy of alcoholic hepatitis. *Gastroenterology* 1989;9:675-80.
- Dominguez M, et al. The ABIC score: a new tool for predicting survival in alcoholic hepatitis. *Gastroenterology* 2008;135:865-73.
- Kamath PS, et al. A model to predict survival in patients with end-stage liver disease. *Hepatology* 2001;33:464-70.

## License

MIT License. See [LICENSE](LICENSE).
