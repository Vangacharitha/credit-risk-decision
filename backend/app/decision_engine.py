from typing import Tuple


def get_risk_tier(risk_score: float) -> str:
    """
    Convert risk score (0 to 100) into a tier.
    Lower score means lower default risk.
    """
    if risk_score < 30:
        return "Low"
    if risk_score < 60:
        return "Medium"
    if risk_score < 80:
        return "High"
    return "Very High"


def get_recommended_decision(risk_score: float) -> str:
    """
    Decision policy:
    - Low risk -> approve
    - Medium/High -> conditional approve
    - Very High -> decline
    """
    if risk_score < 30:
        return "Approve"
    if risk_score < 80:
        return "Conditional Approve"
    return "Decline"


def get_confidence(default_probability: float) -> float:
    """
    Confidence is distance from 50%.
    Closer to 0 or 1 means stronger confidence.
    """
    return round(max(default_probability, 1 - default_probability), 4)