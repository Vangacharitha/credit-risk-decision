import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

from .config import MODEL_PATH, META_PATH, MODEL_VERSION


class ModelService:
    """
    Handles model loading, prediction, and explainability.
    """

    def __init__(self):
        self.pipeline = None
        self.meta = None

    def load_model(self):
        self.pipeline = joblib.load(MODEL_PATH)
        self.meta = joblib.load(META_PATH)

    def ensure_model_loaded(self):
        if self.pipeline is None:
            self.load_model()

    def predict_default_probability(self, input_payload: Dict[str, Any]) -> float:
        self.ensure_model_loaded()

        df = pd.DataFrame([input_payload])
        prob_default = self.pipeline.predict_proba(df)[0][1]  # probability of class 1 (default)
        return float(prob_default)

    def explain_prediction(self, input_payload: Dict[str, Any], top_n: int = 5) -> List[Dict[str, str]]:
        """
        Random-Forest-friendly explainability:
        contribution = transformed_feature_value * feature_importance
        """
        self.ensure_model_loaded()

        preprocessor = self.pipeline.named_steps["preprocessor"]
        model = self.pipeline.named_steps["model"]

        df = pd.DataFrame([input_payload])
        transformed = preprocessor.transform(df)

        # Convert sparse matrix to dense array if needed
        if hasattr(transformed, "toarray"):
            transformed = transformed.toarray()

        feature_names = preprocessor.get_feature_names_out()
        feature_importances = model.feature_importances_

        contributions = transformed[0] * feature_importances

        rows = []
        for name, value in zip(feature_names, contributions):
            rows.append((name, float(value)))

        # Sort by absolute impact
        rows = sorted(rows, key=lambda x: abs(x[1]), reverse=True)[:top_n]

        explanations = []
        for feat, impact_value in rows:
            impact = "Increases Risk" if impact_value >= 0 else "Reduces Risk"
            reason = self._to_plain_language(feat, impact)
            explanations.append(
                {
                    "factor": feat,
                    "impact": impact,
                    "plain_language_reason": reason,
                }
            )

        return explanations

    def _to_plain_language(self, feature_name: str, impact: str) -> str:
        # Convert technical transformed feature name into readable text.
        clean_name = feature_name.replace("num__", "").replace("cat__", "")
        impact_text = "increasing risk" if impact == "Increases Risk" else "reducing risk"

        if clean_name.startswith("employment_type_"):
            category = clean_name.replace("employment_type_", "").replace("_", " ")
            return f"The employment type ({category}) is {impact_text} for this application."
        if clean_name.startswith("residence_type_"):
            category = clean_name.replace("residence_type_", "").replace("_", " ")
            return f"The residence type ({category}) is {impact_text} for this application."
        if clean_name == "monthly_income":
            return f"Monthly income is {impact_text} for repayment confidence."
        if clean_name == "credit_card_utilization":
            return f"Credit card utilization is {impact_text} based on credit usage pattern."
        if clean_name == "missed_payments_last_12m":
            return f"Recent missed payments are {impact_text} in the model decision."
        if clean_name == "utility_payment_score":
            return f"Utility payment behavior is {impact_text} in this risk assessment."
        if clean_name == "mobile_recharge_consistency":
            return f"Mobile recharge consistency is {impact_text} in this assessment."

        return f"{clean_name.replace('_', ' ').title()} is {impact_text} for this application."

    @property
    def model_version(self) -> str:
        if self.meta and "model_version" in self.meta:
            return self.meta["model_version"]
        return MODEL_VERSION