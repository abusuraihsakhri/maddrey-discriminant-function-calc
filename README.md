# Maddrey Discriminant Function Calculator

Clinical reference implementation of three scoring methods used in alcohol-associated hepatitis (AH). The browser calculator runs without a backend.

## Features

- **Modified Maddrey Discriminant Function (mDF):** `4.6 × (patient PT − control PT) + total bilirubin (mg/dL)`. The historical severe threshold is **≥32**.
- **ABIC:** `0.1 × age + 0.08 × bilirubin + 0.8 × INR + 0.3 × creatinine`. Risk strata: **<6.71**, **6.71–<9.0**, **≥9.0**. The original derivation reported approximate **90-day** survival of 100%, 70%, and 25% by stratum; these are cohort observations, not individualized predictions.
- **Classic MELD:** the historical bilirubin–INR–creatinine formula; **not MELD 3.0 or a transplant-allocation calculator**.
- A standalone **HTML/JavaScript interface**, Python CLI, CSV batch processing, FHIR helper, longitudinal monitoring, and separate FastAPI audit/chat demonstration endpoints.

All score outputs are for education and decision support, not diagnosis or medication authorization. The 2024 ACG guideline emphasizes MELD >20 and contraindication assessment in severe AH. The limited corticosteroid screen in the Python API is **not** comprehensive clearance for treatment.

## Browser use

Open `web/index.html` in a current browser. Enter patient PT, the **local laboratory's normal control PT**, and total serum bilirubin in **mg/dL**; expand the optional section to add age, INR, and creatinine. The page calculates entirely in JavaScript.

**Privacy:** The browser calculator does not make API calls or persist submitted values. Do not enter patient names or identifiers. The Python CLI reads local files; the optional API runs a separate in-memory audit demonstration and must not be deployed publicly without additional access controls and security review. The regex identifier guard is not a comprehensive PHI de-identification system.

## Python installation and CLI

Python 3.10 or later:

```bash
python -m pip install -e ".[dev]"
python cli.py mdf --pt-patient 17 --pt-control 12 --bilirubin 10
python cli.py abic --age 50 --bilirubin 10 --inr 1.5 --creatinine 1
python cli.py meld --bilirubin 5 --inr 2 --creatinine 1.5
python cli.py comprehensive --pt-patient 17 --pt-control 12 --bilirubin 10 --age 50 --inr 1.5 --creatinine 1
python cli.py batch -i sample.csv -o results.csv --score mdf
```

For batch mDF, input columns are `pt_patient,pt_control,bilirubin`. Other modes require the corresponding clinical inputs; missing values are rejected rather than silently filled with defaults.

Programmatic example:

```python
from maddrey_df import calculate_maddrey_df, calculate_abic

print(calculate_maddrey_df(17, 12, 10)["mdf_score"])  # 33.0
print(calculate_abic(50, 10, 1.5, 1)["abic_score"])  # 7.3
```

The FHIR helper requires a **laboratory-provided control PT**; LOINC 5960-0 is deprecated and **not** a general control PT code. Supported input units are seconds for PT, and mg/dL or µmol/L for bilirubin.

## API and container

```bash
AUDIT_SECRET_KEY="replace-with-a-long-random-secret" docker compose up --build
```

This serves the separate FastAPI demonstration locally at `http://127.0.0.1:8000` (including `/health`, `/api/audit` and `/api/chat`). Docker requires a configured signing key. Its audit chain is process-local; it is not durable, certified, or suitable as a clinical EHR audit record. The API is not needed for the browser calculator.

## Tests and compatibility

```bash
python -m pytest -q
node --test tests_js/calculator.test.cjs
```

GitHub Actions runs Python 3.10–3.12 and Node 22 checks. The static page uses standard HTML, CSS, and vanilla JavaScript (no runtime packages), intended for current evergreen desktop and mobile browsers. Its GitHub Pages workflow publishes the `web/` directory from `master`.

## References

- Maddrey WC et al. *Corticosteroid therapy of alcoholic hepatitis*. Gastroenterology. 1978;75:193–199.
- Domínguez M et al. *A new scoring system for prognostic stratification of patients with alcoholic hepatitis*. Am J Gastroenterol. 2008;103:2747–2756. [PubMed](https://pubmed.ncbi.nlm.nih.gov/18721242/).
- Jophlin LL et al. *ACG Clinical Guideline: Alcohol-Associated Liver Disease*. Am J Gastroenterol. 2024. [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11040545/).

## License

MIT. See [LICENSE](LICENSE).
