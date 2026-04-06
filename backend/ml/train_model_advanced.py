from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split

try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    HAS_PLOTS = True
except Exception:
    HAS_PLOTS = False

try:
    from ml.train_model import generate_synthetic_data
except ModuleNotFoundError:
    from train_model import generate_synthetic_data


FEATURE_COLUMNS = [
    "skill_match_ratio",
    "willingness_score",
    "availability_hours",
    "distance_km",
    "urgency_level",
    "fairness_score",
    "reliability_score",
    "time_compatibility",
    "task_difficulty",
    "ngo_reputation",
    "distance_score",
    "urgency_score",
    "volunteer_aicte_points",
    "volunteer_aicte_norm",
    "task_points_possible",
    "task_points_norm",
]


def _load_or_generate_matches_csv(data_dir: Path) -> pd.DataFrame:
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "volunteer_task_matches.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        missing = [c for c in FEATURE_COLUMNS + ["match_success"] if c not in df.columns]
        if not missing:
            return df

    _, _, df_matches = generate_synthetic_data(n_volunteers=500, n_tasks=300, n_matches=2000)
    df_matches.to_csv(csv_path, index=False)
    return df_matches


def run_advanced_training(quick: bool = False) -> dict:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    outputs_dir = base_dir / "advanced_outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    df_matches = _load_or_generate_matches_csv(data_dir)
    X = df_matches[FEATURE_COLUMNS]
    y = df_matches["match_success"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Baseline
    rf_baseline = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_baseline.fit(X_train, y_train)
    y_pred_baseline = rf_baseline.predict(X_test)
    y_prob_baseline = rf_baseline.predict_proba(X_test)[:, 1]
    cv_scores = cross_val_score(rf_baseline, X_train, y_train, cv=5, scoring="f1")

    baseline_metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred_baseline)),
        "precision": float(precision_score(y_test, y_pred_baseline, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred_baseline, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred_baseline, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob_baseline)),
        "cv_f1_mean": float(cv_scores.mean()),
        "cv_f1_std": float(cv_scores.std()),
    }

    # Hyperparameter tuning
    if quick:
        param_grid = {
            "n_estimators": [100, 200],
            "max_depth": [10, 20, None],
            "min_samples_split": [2, 5],
            "min_samples_leaf": [1, 2],
            "max_features": ["sqrt"],
        }
    else:
        param_grid = {
            "n_estimators": [100, 200, 300],
            "max_depth": [10, 20, 30, None],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
            "max_features": ["sqrt", "log2"],
        }

    grid_search = GridSearchCV(
        RandomForestClassifier(random_state=42, n_jobs=-1),
        param_grid,
        cv=3,
        scoring="f1",
        verbose=1,
        n_jobs=-1,
    )
    grid_search.fit(X_train, y_train)

    rf_final = grid_search.best_estimator_
    y_pred_final = rf_final.predict(X_test)
    y_prob_final = rf_final.predict_proba(X_test)[:, 1]
    cm = confusion_matrix(y_test, y_pred_final)

    final_metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred_final)),
        "precision": float(precision_score(y_test, y_pred_final, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred_final, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred_final, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob_final)),
        "confusion_matrix": cm.tolist(),
        "best_params": grid_search.best_params_,
        "best_cv_f1": float(grid_search.best_score_),
        "classification_report": classification_report(
            y_test, y_pred_final, target_names=["No Match", "Match"], output_dict=True
        ),
    }

    feature_importance = (
        pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": rf_final.feature_importances_})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )

    # Save artifacts
    model_path = outputs_dir / "swam_random_forest_model.pkl"
    features_path = outputs_dir / "model_features.pkl"
    metrics_path = outputs_dir / "advanced_metrics.json"
    importance_path = outputs_dir / "feature_importance.csv"

    joblib.dump(rf_final, model_path)
    joblib.dump(FEATURE_COLUMNS, features_path)
    feature_importance.to_csv(importance_path, index=False)

    summary = {
        "dataset": {
            "records": int(len(df_matches)),
            "success_rate": float(y.mean()),
            "train_size": int(len(X_train)),
            "test_size": int(len(X_test)),
            "feature_count": len(FEATURE_COLUMNS),
        },
        "baseline": baseline_metrics,
        "final": final_metrics,
        "artifacts": {
            "model": str(model_path),
            "features": str(features_path),
            "metrics": str(metrics_path),
            "feature_importance": str(importance_path),
        },
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if HAS_PLOTS:
        sns.set_style("whitegrid")
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        top = feature_importance.head(10)
        axes[0].barh(top["feature"], top["importance"], color="steelblue")
        axes[0].invert_yaxis()
        axes[0].set_title("Top Feature Importance")

        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            ax=axes[1],
            xticklabels=["No Match", "Match"],
            yticklabels=["No Match", "Match"],
        )
        axes[1].set_title("Confusion Matrix")
        axes[1].set_xlabel("Predicted")
        axes[1].set_ylabel("Actual")

        fig.tight_layout()
        fig.savefig(outputs_dir / "model_performance_analysis.png", dpi=200, bbox_inches="tight")
        plt.close(fig)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced RF training with tuning and metrics.")
    parser.add_argument("--quick", action="store_true", help="Use smaller grid for faster execution.")
    args = parser.parse_args()

    result = run_advanced_training(quick=args.quick)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

