
```markdown
# Credit Risk Decisioning Platform

An end-to-end credit risk decisioning project with:

- **FastAPI backend** for model training, prediction, and analytics APIs
- **Streamlit frontend** for loan intake, underwriter workflows, portfolio monitoring, and fairness reporting
- **SQLite audit store** for application decisions and model outputs
- **Random Forest ML pipeline** with preprocessing and hyperparameter tuning

---

## Features

- Loan application scoring with `risk_score` (0-100)
- Risk tier mapping: **Low / Medium / High / Very High**
- Automated decision recommendation: **Approve / Conditional Approve / Decline**
- Top factor explainability (human-readable reasons)
- Alternative data enrichment (consent-based)
- Underwriter queue and application detail APIs
- Portfolio summary, model metrics, score trend, and fairness report by gender

---

## Project Structure

```text
credit_risk_decision/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ schemas.py
│  │  ├─ model_services.py
│  │  ├─ decision_engine.py
│  │  ├─ storage.py
│  │  └─ config.py
│  ├─ data/
│  │  └─ loan_training_data.csv
│  ├─ models/
│  │  ├─ credit_risk_pipeline.joblib
│  │  ├─ model_meta.joblib
│  │  └─ applications.db
│  └─ scripts/
│     └─ train_model.py
└─ frontend/
   └─ streamlit_app.py
```

---

## Tech Stack

- Python
- FastAPI + Uvicorn
- Streamlit
- scikit-learn
- pandas, numpy
- SQLite
- joblib

---

## Setup

### 1) Create and activate virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

If you already have a `requirements.txt`, use:
```bash
pip install -r requirements.txt
```

Otherwise, install minimum required packages:
```bash
pip install fastapi uvicorn streamlit requests pandas numpy scikit-learn joblib pydantic
```

---

## Running the Project

## A) Start Backend (FastAPI)

From project root:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

Backend base URL:
- `http://127.0.0.1:8001`

Health check:
- `GET /` returns API running message.

---

## B) Train Model (first time or retrain)

Option 1: Train via API endpoint:
```http
POST /train-model
```

Option 2: Train using script:
```bash
python -m backend.scripts.train_model
```

This saves:
- `backend/models/credit_risk_pipeline.joblib`
- `backend/models/model_meta.joblib`

---

## C) Start Frontend (Streamlit)

In a new terminal:
```bash
streamlit run frontend/streamlit_app.py
```

Optional backend URL override:
```powershell
$env:BACKEND_URL="http://127.0.0.1:8001"
streamlit run frontend/streamlit_app.py
```

---

## API Endpoints

- `GET /`  
  API status check.

- `POST /train-model`  
  Trains model from CSV and loads it in memory.

- `POST /predict`  
  Scores one loan application and returns:
  - risk score
  - risk tier
  - recommended decision
  - confidence
  - top factor explanations
  - applicant + underwriter messages
  - enrichment output

- `GET /applications`  
  Underwriter queue (recent applications).

- `GET /applications/{application_id}`  
  Full details for one application.

- `GET /portfolio-summary`  
  Portfolio-level counts, distributions, average score.

- `GET /model-metrics`  
  Approval/conditional/decline rates + expected default proxy.

- `GET /fairness-report`  
  Segment-level rates grouped by gender.

- `GET /score-trend`  
  Daily average risk score and application volume.

---

## Example Prediction Payload

```json
{
  "age": 30,
  "monthly_income": 40000,
  "employment_years": 3,
  "existing_loan_amount": 50000,
  "loan_amount_requested": 150000,
  "loan_tenure_months": 36,
  "credit_card_utilization": 50,
  "missed_payments_last_12m": 1,
  "utility_payment_score": 75,
  "mobile_recharge_consistency": 70,
  "employment_type": "salaried",
  "residence_type": "owned",
  "gender": "male",
  "consent_for_alt_data": true
}
```

---

## Decision Logic

- **Risk tier**
  - `< 30` -> Low
  - `30-59.99` -> Medium
  - `60-79.99` -> High
  - `>= 80` -> Very High

- **Recommended decision**
  - Low -> Approve
  - Medium/High -> Conditional Approve
  - Very High -> Decline

---

## Data & Model Notes

- Training data path: `backend/data/loan_training_data.csv`
- Target column: `defaulted`
- Model: `RandomForestClassifier`
- Search strategy: `RandomizedSearchCV` with F1 refit
- Metadata includes ROC-AUC, F1, Precision, Recall, confusion matrix format:
  - `[[TN, FP], [FN, TP]]`

---

## Database / Audit Trail

SQLite DB: `backend/models/applications.db`  
Stores:
- `created_at`
- `model_version`
- raw `input_data` JSON
- raw `output_data` JSON

This acts as decision logging for underwriter review and analytics.

---

## Notes for Production Hardening

- Restrict CORS (currently open for demo)
- Add authentication and role-based access
- Add request/response validation hardening and rate limiting
- Add model monitoring and drift checks
- Use proper fairness/ethics evaluation beyond basic segment reporting
- Containerize + CI/CD + environment-specific config

---

## License

For academic/demo use unless otherwise specified.
```
