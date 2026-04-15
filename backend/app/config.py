from pathlib import Path

# Base folder of backend
BASE_DIR = Path(__file__).resolve().parent.parent

# File paths used in the project
MODEL_PATH = BASE_DIR / "models" / "credit_risk_pipeline.joblib"
META_PATH = BASE_DIR / "models" / "model_meta.joblib"
DB_PATH = BASE_DIR / "models" / "applications.db"
TRAINING_DATA_PATH = BASE_DIR / "data" / "loan_training_data.csv"

# Model version (update when you retrain if needed)
MODEL_VERSION = "v1.0"