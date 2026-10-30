"""Train and compare heart-disease models. Run from the project root: python -m ml.train_risk_model"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "raw" / "heart.csv"
OUT = ROOT / "ml" / "artifacts"
NUMERIC = ["Age", "RestingBP", "Cholesterol", "FastingBS", "MaxHR", "Oldpeak"]
CATEGORICAL = ["Sex", "ChestPainType", "RestingECG", "ExerciseAngina", "ST_Slope"]

CANDIDATES = {
    "logistic_regression": LogisticRegression(max_iter=1000),
    "random_forest": RandomForestClassifier(n_estimators=300, random_state=42),
    "xgboost": XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                             eval_metric="logloss", random_state=42),
}


def load_data():
    df = pd.read_csv(DATA)
    # In this dataset 0 means "not measured", so treat it as missing
    df[["Cholesterol", "RestingBP"]] = df[["Cholesterol", "RestingBP"]].replace(0, np.nan)
    return df[NUMERIC + CATEGORICAL], df["HeartDisease"]


def build_pipeline(classifier):
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    prep = ColumnTransformer([("num", numeric, NUMERIC), ("cat", categorical, CATEGORICAL)])
    return Pipeline([("prep", prep), ("clf", classifier)])


def main():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    pipelines, results = {}, {}
    for name, classifier in CANDIDATES.items():
        pipe = build_pipeline(classifier)
        cv_auc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc").mean()
        pipe.fit(X_train, y_train)
        proba = pipe.predict_proba(X_test)[:, 1]
        pred = (proba >= 0.5).astype(int)
        results[name] = {
            "cv_roc_auc": round(cv_auc, 3),
            "test_accuracy": round(accuracy_score(y_test, pred), 3),
            "test_precision": round(precision_score(y_test, pred), 3),
            "test_recall": round(recall_score(y_test, pred), 3),
            "test_f1": round(f1_score(y_test, pred), 3),
            "test_roc_auc": round(roc_auc_score(y_test, proba), 3),
        }
        pipelines[name] = pipe
        print(name, results[name])

    best = max(results, key=lambda n: results[n]["cv_roc_auc"])
    OUT.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipelines[best], OUT / "risk_model.joblib")
    metrics = {"best_model": best, "train_rows": len(X_train), "test_rows": len(X_test),
               "features": NUMERIC + CATEGORICAL, "medians": X_train[NUMERIC].median().to_dict(),
               "models": results}
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    display = ConfusionMatrixDisplay.from_estimator(pipelines[best], X_test, y_test,
                                                    display_labels=["No disease", "Disease"])
    display.figure_.savefig(OUT / "confusion_matrix.png", dpi=150, bbox_inches="tight")
    print("Best model:", best)


if __name__ == "__main__":
    main()