from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    LoanApplicationInput,
    PredictionResponse,
    TrainResponse,
    PortfolioSummaryResponse,
    ModelMetricsResponse,
    FairnessReportResponse,
    ScoreTrendPoint,
)
from .model_services import ModelService
from .decision_engine import get_risk_tier, get_recommended_decision, get_confidence
from .storage import (
    init_db,
    save_application,
    list_applications,
    get_application_by_id,
    portfolio_summary,
    model_metrics,
    fairness_report_by_gender,
    score_trend,
)
from .config import MODEL_VERSION

# We import training function so backend can train model on demand
from backend.scripts.train_model import train_and_save_model


app = FastAPI(title="Loan Credit Risk Decisioning API", version="1.0")

# Allow Streamlit frontend to call backend API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For assignment/demo use. In production, use specific domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_service = ModelService()


MODEL_FEATURES = [
    "age",
    "monthly_income",
    "employment_years",
    "existing_loan_amount",
    "loan_amount_requested",
    "loan_tenure_months",
    "credit_card_utilization",
    "missed_payments_last_12m",
    "utility_payment_score",
    "mobile_recharge_consistency",
    "employment_type",
    "residence_type",
]


def run_alt_data_enrichment(payload: dict) -> dict:
    """
    Beginner-friendly enrichment pipeline.
    We only compute extra indicators if user consent is provided.
    """
    if not payload.get("consent_for_alt_data", False):
        return {"enrichment_status": "skipped_no_consent"}

    monthly_income = max(float(payload.get("monthly_income", 0.0)), 1.0)
    existing_loan = float(payload.get("existing_loan_amount", 0.0))
    requested_loan = float(payload.get("loan_amount_requested", 0.0))
    missed = int(payload.get("missed_payments_last_12m", 0))

    liability_to_income_ratio = round((existing_loan + requested_loan) / (monthly_income * 12), 3)
    payment_behavior_index = round(
        (float(payload.get("utility_payment_score", 0.0)) + float(payload.get("mobile_recharge_consistency", 0.0))) / 2,
        2,
    )
    behavior_risk_flag = "high" if (missed >= 3 or payment_behavior_index < 45) else "normal"

    return {
        "enrichment_status": "applied",
        "liability_to_income_ratio": liability_to_income_ratio,
        "payment_behavior_index": payment_behavior_index,
        "behavior_risk_flag": behavior_risk_flag,
    }


def build_applicant_message(decision: str, top_factors: list) -> str:
    if decision == "Approve":
        return "Your loan is approved based on strong overall repayment indicators."
    if decision == "Conditional Approve":
        return "Your loan is conditionally approved. Final approval depends on additional verification."
    key_reasons = [f.get("plain_language_reason", "") for f in top_factors[:3] if f.get("impact") == "Increases Risk"]
    if key_reasons:
        return "Your loan is declined mainly due to: " + "; ".join(key_reasons)
    return "Your loan is declined because the current profile indicates higher repayment risk."


def build_underwriter_summary(risk_score: float, risk_tier: str, decision: str) -> str:
    return (
        f"Model risk score is {risk_score} ({risk_tier}). "
        f"Recommended action: {decision}. Please review top factors before final decision."
    )


@app.on_event("startup")
def startup_event():
    init_db()
    try:
        model_service.load_model()
    except Exception:
        # Model may not exist on first run. User can call /train-model.
        pass


@app.get("/")
def root():
    return {"message": "Credit Risk Decisioning API is running"}


@app.post("/train-model", response_model=TrainResponse)
def train_model():
    """
    Train the model from CSV and save artifacts.
    """
    train_and_save_model()
    model_service.load_model()
    return TrainResponse(message="Model trained and loaded successfully.", model_version=MODEL_VERSION)


@app.post("/predict", response_model=PredictionResponse)
def predict(application: LoanApplicationInput):
    """
    Score one loan application and return:
    - risk score
    - tier
    - decision
    - explainability factors
    """
    try:
        payload = application.dict()
        enriched_data = run_alt_data_enrichment(payload)
        model_payload = {k: payload[k] for k in MODEL_FEATURES}
        prob_default = model_service.predict_default_probability(model_payload)

        # Risk score from probability (0 to 100)
        risk_score = round(prob_default * 100, 2)
        risk_tier = get_risk_tier(risk_score)
        decision = get_recommended_decision(risk_score)
        confidence = get_confidence(prob_default)

        top_factors = model_service.explain_prediction(model_payload, top_n=5)
        applicant_message = build_applicant_message(decision, top_factors)
        underwriter_summary = build_underwriter_summary(risk_score, risk_tier, decision)

        output_data = {
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "recommended_decision": decision,
            "confidence": confidence,
            "top_factors": top_factors,
            "applicant_message": applicant_message,
            "underwriter_summary": underwriter_summary,
            "enriched_data": enriched_data,
        }

        app_id = save_application(payload, output_data, model_service.model_version)

        return PredictionResponse(
            application_id=app_id,
            risk_score=risk_score,
            risk_tier=risk_tier,
            recommended_decision=decision,
            confidence=confidence,
            top_factors=top_factors,
            applicant_message=applicant_message,
            underwriter_summary=underwriter_summary,
            enriched_data=enriched_data,
            model_version=model_service.model_version,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/applications")
def get_applications():
    """
    Underwriter queue endpoint.
    """
    return list_applications()


@app.get("/applications/{application_id}")
def get_application_details(application_id: int):
    """
    Full application detail endpoint.
    """
    data = get_application_by_id(application_id)
    if not data:
        raise HTTPException(status_code=404, detail="Application not found")
    return data


@app.get("/portfolio-summary", response_model=PortfolioSummaryResponse)
def get_portfolio_summary():
    return portfolio_summary()


@app.get("/model-metrics", response_model=ModelMetricsResponse)
def get_model_performance_metrics():
    return model_metrics()


@app.get("/fairness-report", response_model=list[FairnessReportResponse])
def get_fairness_report():
    return fairness_report_by_gender()


@app.get("/score-trend", response_model=list[ScoreTrendPoint])
def get_score_trend():
    return score_trend()