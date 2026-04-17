# Credit Risk Decisioning Platform

An end-to-end credit risk decisioning project with:

- **FastAPI backend** for model training, prediction, and analytics APIs  
- **Streamlit frontend** for loan intake, underwriter workflows, portfolio monitoring, and fairness reporting  
- **SQLite audit store** for application decisions and model outputs  
- **Random Forest ML pipeline** with preprocessing and hyperparameter tuning  

---

## Features

- Loan application scoring with `risk_score` (0–100)  
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

### 1) Create virtual environment

```bash
python -m venv .venv
```

Activate:

**Windows**
```bash
.venv\Scripts\activate
```

---

### 2) Install dependencies

```bash
pip install fastapi uvicorn streamlit requests pandas numpy scikit-learn joblib pydantic
```

---

## Running the Project

### A) Start Backend (FastAPI)

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

API URL:
```
http://127.0.0.1:8001
```

---

### B) Train Model

```bash
python -m backend.scripts.train_model
```

OR via API:

```
POST /train-model
```

---

### C) Start Frontend (Streamlit)

```bash
streamlit run frontend/streamlit_app.py
```

---

## API Endpoints

- `GET /` → Health check  
- `POST /train-model` → Train ML model  
- `POST /predict` → Get risk score + decision  
- `GET /applications` → Underwriter queue  
- `GET /applications/{id}` → Application details  
- `GET /portfolio-summary` → Portfolio analytics  
- `GET /model-metrics` → Model performance  
- `GET /fairness-report` → Bias/fairness view  
- `GET /score-trend` → Score analytics  

---

## Example Request

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

## Decision Rules

- **Low (<30)** → Approve  
- **Medium (30–59)** → Conditional Approve  
- **High (60–79)** → Conditional Approve  
- **Very High (≥80)** → Decline  

---

## Database

SQLite file:
```
backend/models/applications.db
```

Stores:
- Inputs  
- Predictions  
- Model version  
- Timestamp  

---
