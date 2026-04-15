from pydantic import BaseModel, Field
from typing import List, Dict, Any


class LoanApplicationInput(BaseModel):
    # Basic structured data
    age: int = Field(..., ge=18, le=75)
    monthly_income: float = Field(..., gt=0)
    employment_years: float = Field(..., ge=0)
    existing_loan_amount: float = Field(..., ge=0)
    loan_amount_requested: float = Field(..., gt=0)
    loan_tenure_months: int = Field(..., ge=6, le=360)

    # Credit and repayment behavior
    credit_card_utilization: float = Field(..., ge=0, le=100)  # percent
    missed_payments_last_12m: int = Field(..., ge=0, le=24)

    # Alternative data signals
    utility_payment_score: float = Field(..., ge=0, le=100)
    mobile_recharge_consistency: float = Field(..., ge=0, le=100)

    # Categorical fields
    employment_type: str  # salaried / self_employed / unemployed
    residence_type: str   # owned / rented / family
    gender: str  # male / female / other
    consent_for_alt_data: bool = False


class FactorExplanation(BaseModel):
    factor: str
    impact: str
    plain_language_reason: str


class PredictionResponse(BaseModel):
    application_id: int
    risk_score: float
    risk_tier: str
    recommended_decision: str
    confidence: float
    top_factors: List[FactorExplanation]
    applicant_message: str
    underwriter_summary: str
    enriched_data: Dict[str, Any]
    model_version: str


class TrainResponse(BaseModel):
    message: str
    model_version: str


class PortfolioSummaryResponse(BaseModel):
    total_applications: int
    risk_tier_distribution: Dict[str, int]
    decision_distribution: Dict[str, int]
    average_risk_score: float


class ModelMetricsResponse(BaseModel):
    approval_rate: float
    conditional_approval_rate: float
    decline_rate: float
    average_risk_score: float
    expected_default_rate: float


class FairnessReportResponse(BaseModel):
    segment: str
    total_applications: int
    approval_rate: float
    conditional_approval_rate: float
    decline_rate: float


class ScoreTrendPoint(BaseModel):
    date: str
    average_risk_score: float
    application_count: int