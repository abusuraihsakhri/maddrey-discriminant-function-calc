# Maddrey Discriminant Function Calc

> **Domain:** Gastroenterology, Hepatology & Clinical Nutrition
> **Reference Guidelines:** AASLD & ACG Clinical Practice Guidelines

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)

---

## What It Does

Clinical scoring calculator for alcoholic hepatitis severity assessment. Computes:

- **Maddrey Discriminant Function (mDF)** — severity classification and corticosteroid indication
- **ABIC Score** — age-bilirubin-INR-creatinine prognostic score
- **MELD Score** — model for end-stage liver disease
- **Steroid Eligibility** — contraindication-aware corticosteroid recommendation

Author: Dr. Abu Suraih Sakhri | License: MIT

---

## Installation

```bash
pip install -e .
```

For development with testing:
```bash
pip install -e ".[dev]"
```

---

## Usage

### CLI — Single Score Calculation

```bash
# Maddrey DF
python cli.py mdf --pt-patient 17.0 --pt-control 12.0 --bilirubin 10.0

# ABIC Score
python cli.py abic --age 55 --bilirubin 15.0 --inr 2.0 --creatinine 1.5

# MELD Score
python cli.py meld --bilirubin 5.0 --inr 2.0 --creatinine 1.5

# Steroid Eligibility
python cli.py steroid --mdf 40.0

# Comprehensive Assessment (all scores)
python cli.py comprehensive --pt-patient 18.0 --pt-control 12.0 --bilirubin 15.0 --age 55 --inr 2.0 --creatinine 1.5
```

### CLI — Batch Processing

```bash
python cli.py batch -i input.csv -o results.csv --score mdf
```

CSV columns for mdf: `pt_patient`, `pt_control`, `bilirubin`

### Multi-Agent Audit & LLM Reasoning

```bash
# Run multi-agent audit evaluation
python cli.py audit --task-id TASK-01 --primary 12.0 --secondary 4.0

# Query LLM reasoning adapter
python cli.py chat "Explain mDF thresholds"

# Verify HMAC audit chain integrity
python cli.py verify-audit
```

### Programmatic API

```python
from maddrey_df import calculate_maddrey_df, calculate_abic, calculate_meld, comprehensive_assessment

result = calculate_maddrey_df(pt_patient=17.0, pt_control=12.0, bilirubin_mg_dl=10.0)
print(result["mdf_score"])  # 33.0
print(result["severity"])   # "Severe"
```

### FastAPI REST Server

```bash
uvicorn agents.api:app --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /health` — service health check
- `GET /metrics` — Prometheus operational metrics
- `POST /api/audit` — submit task for multi-agent evaluation
- `POST /api/chat` — LLM reasoning query
- `GET /api/audit/logs` — HMAC audit trail

---

## Mathematical Formulation

**Maddrey DF:** `mDF = 4.6 × (PT_patient − PT_control) + Bilirubin`
- <32: Mild — supportive care
- ≥32: Severe — consider corticosteroids

**ABIC:** `(Age × 0.1) + (Bilirubin × 0.08) + (INR × 0.1) + (Creatinine × 0.3)`
- <6.71: Low risk (~100% 1-year survival)
- 6.71–8.99: Intermediate (~70%)
- ≥9.0: High risk (~25%)

**MELD:** `3.78 × ln(Bilirubin) + 11.2 × ln(INR) + 9.57 × ln(Creatinine) + 6.43`
- Values clamped per UNO/OPTN convention (min 1.0, creatinine capped at 4.0)

---

## Input Validation

All clinical parameters are validated against physiological bounds:

| Parameter | Range | Unit |
|-----------|-------|------|
| PT (patient/control) | 5–120 | seconds |
| Bilirubin | 0–75 | mg/dL |
| INR | 0.5–15 | dimensionless |
| Creatinine | 0.1–30 | mg/dL |
| Age | 0–120 | years |

---

## Security

- **Zero-PHI Outbound Guard:** AST and regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers
- **HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Configurable Secret:** Set `AUDIT_SECRET_KEY` environment variable in production (never use defaults)

---

## Testing

```bash
pytest -v
```

---

## Container Deployment

```bash
docker build -t maddrey-discriminant-function-calc .
docker run -e AUDIT_SECRET_KEY=your-secret-key -p 8000:8000 maddrey-discriminant-function-calc
```

Or with docker-compose:
```bash
AUDIT_SECRET_KEY=your-secret-key docker compose up
```

---

## References

- Maddrey WC, et al. *Hepatology* 1989;9:675–80.
- Dominguez M, et al. *Gastroenterology* 2008;135:865–73 (ABIC).
- Kamath PS, et al. *Hepatology* 2001;33:464–70 (MELD).
