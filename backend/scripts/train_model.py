import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix, precision_score, recall_score
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

from backend.app.config import TRAINING_DATA_PATH, MODEL_PATH, META_PATH, MODEL_VERSION


def train_and_save_model():
    """
    Train a Random Forest model with hyperparameter tuning
    and save pipeline + metadata.
    """
    # 1) Load dataset
    df = pd.read_csv(TRAINING_DATA_PATH)

    # 2) Define target and features
    target_col = "defaulted"
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # 3) Separate numeric and categorical columns
    numeric_features = [
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
    ]

    categorical_features = [
        "employment_type",
        "residence_type",
    ]

    # 4) Build preprocessing
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    # 5) Build full model pipeline
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # 6) Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 7) Hyperparameter tuning
    # We optimize for F1 since the target classes are slightly imbalanced.
    param_distributions = {
        "model__n_estimators": [100, 200, 300, 500],
        "model__max_depth": [8, 12, 16, 20, None],
        "model__min_samples_split": [2, 5, 8, 12],
        "model__min_samples_leaf": [1, 2, 3, 5],
        "model__max_features": ["sqrt", "log2", None],
        "model__class_weight": [None, "balanced"],
    }

    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=param_distributions,
        n_iter=20,
        scoring={"f1": "f1", "roc_auc": "roc_auc"},
        refit="f1",
        cv=3,
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )
    search.fit(X_train, y_train)
    best_pipeline = search.best_estimator_

    # 8) Evaluate best tuned model
    preds = best_pipeline.predict(X_test)
    probs = best_pipeline.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, probs)
    f1 = f1_score(y_test, preds, pos_label=1)
    precision = precision_score(y_test, preds, pos_label=1)
    recall = recall_score(y_test, preds, pos_label=1)
    conf_matrix = confusion_matrix(y_test, preds).tolist()

    # 9) Save model and metadata
    joblib.dump(best_pipeline, MODEL_PATH)
    meta = {
        "model_version": MODEL_VERSION,
        "model_type": "RandomForestClassifier",
        "cv_best_params": search.best_params_,
        "cv_best_f1": round(float(search.best_score_), 4),
        "roc_auc": round(float(auc), 4),
        "f1_score_default_class": round(float(f1), 4),
        "precision_default_class": round(float(precision), 4),
        "recall_default_class": round(float(recall), 4),
        "confusion_matrix": conf_matrix,  # [[TN, FP], [FN, TP]]
        "features": list(X.columns),
        "target": target_col,
    }
    joblib.dump(meta, META_PATH)

    print("Model training complete.")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved metadata to: {META_PATH}")
    print(f"Best hyperparameters: {meta['cv_best_params']}")
    print(f"Best CV F1: {meta['cv_best_f1']}")
    print(
        "ROC-AUC: {0}, F1(default=1): {1}, Precision: {2}, Recall: {3}".format(
            meta["roc_auc"],
            meta["f1_score_default_class"],
            meta["precision_default_class"],
            meta["recall_default_class"],
        )
    )
    print(f"Confusion Matrix [[TN, FP], [FN, TP]]: {meta['confusion_matrix']}")


if __name__ == "__main__":
    train_and_save_model()