from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

BANGALORE_CENTER = (12.9716, 77.5946)
SKILLS = [
    "teaching",
    "mentoring",
    "fundraising",
    "event_planning",
    "social_media",
    "graphic_design",
    "photography",
    "writing",
    "public_speaking",
    "coding",
    "data_entry",
    "counseling",
    "medical_assistance",
    "legal_advice",
    "community_outreach",
    "translation",
    "cooking",
    "gardening",
    "construction",
]
NGO_TYPES = [
    "education",
    "healthcare",
    "environment",
    "women_empowerment",
    "child_welfare",
    "elderly_care",
    "animal_welfare",
    "disaster_relief",
]

def generate_location(center: Tuple[float, float], max_radius_km: float = 30) -> Tuple[float, float]:
    lat, lon = center
    radius_deg = max_radius_km / 111.0
    angle = random.uniform(0, 2 * np.pi)
    distance = random.uniform(0, radius_deg)
    return round(lat + distance * np.cos(angle), 4), round(lon + distance * np.sin(angle), 4)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return float(r * (2 * np.arcsin(np.sqrt(a))))


def generate_synthetic_data(
    n_volunteers: int = 500,
    n_tasks: int = 300,
    n_matches: int = 2000,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    random.seed(42)
    np.random.seed(42)

    volunteers = []
    for i in range(n_volunteers):
        num_skills = random.randint(2, 6)
        volunteer_skills = random.sample(SKILLS, num_skills)
        v_lat, v_lon = generate_location(BANGALORE_CENTER)
        volunteers.append(
            {
                "volunteer_id": f"V{i+1:04d}",
                "skills": ",".join(volunteer_skills),
                "willingness_score": round(random.uniform(0.4, 1.0), 2),
                "availability_hours_week": random.choice([5, 10, 15, 20, 25, 30, 40]),
                "latitude": v_lat,
                "longitude": v_lon,
                "experience_months": random.randint(0, 60),
                "tasks_completed": random.randint(0, 50),
                "aicte_points": round(random.uniform(0, 500), 1),
                "avg_rating": round(random.uniform(3.0, 5.0), 1),
                "reliability_score": round(random.uniform(0.5, 1.0), 2),
                "preferred_ngo_type": random.choice(NGO_TYPES),
            }
        )

    tasks = []
    for i in range(n_tasks):
        req_skills = random.sample(SKILLS, random.randint(1, 4))
        t_lat, t_lon = generate_location(BANGALORE_CENTER)
        urgency = random.randint(1, 5)
        tasks.append(
            {
                "task_id": f"T{i+1:04d}",
                "ngo_type": random.choice(NGO_TYPES),
                "required_skills": ",".join(req_skills),
                "urgency_level": urgency,
                "duration_hours": random.choice([2, 4, 6, 8, 10, 15, 20]),
                "latitude": t_lat,
                "longitude": t_lon,
                "difficulty_level": random.randint(1, 5),
                "requires_background_check": random.choice([0, 1]),
                "flexible_timing": random.choice([0, 1]),
                "activity_type": random.choice(
                    [
                        "community_service",
                        "teaching",
                        "health_camp",
                        "disaster_relief",
                        "environment",
                        "skill_training",
                        "event_management",
                    ]
                ),
                "points_per_hour": random.choice([2.0, 2.5, 3.0, 4.0]),
                "ngo_reputation_score": round(random.uniform(3.5, 5.0), 1),
            }
        )

    matches = []
    for i in range(n_matches):
        volunteer = volunteers[random.randint(0, n_volunteers - 1)]
        task = tasks[random.randint(0, n_tasks - 1)]

        v_skills = set(volunteer["skills"].split(","))
        t_skills = set(task["required_skills"].split(","))
        skill_overlap = len(v_skills.intersection(t_skills))
        skill_match_ratio = skill_overlap / len(t_skills) if t_skills else 0.0

        distance_km = haversine_distance(
            volunteer["latitude"],
            volunteer["longitude"],
            task["latitude"],
            task["longitude"],
        )
        distance_score = max(0.0, 1.0 - (distance_km / 50.0))
        urgency_score = task["urgency_level"] / 5.0
        time_compatibility = 1.0 if volunteer["availability_hours_week"] >= task["duration_hours"] else 0.5
        fairness_score = max(0.1, 1.0 - (volunteer["tasks_completed"] / 50.0))
        task_points_opportunity = float(task["duration_hours"]) * float(task["points_per_hour"])
        volunteer_aicte_norm = min(float(volunteer["aicte_points"]), 1000.0) / 1000.0
        task_points_norm = min(float(task_points_opportunity), 200.0) / 200.0

        score = (
            0.35 * skill_match_ratio
            + 0.15 * volunteer["willingness_score"]
            + 0.15 * distance_score
            + 0.10 * time_compatibility
            + 0.10 * fairness_score
            + 0.10 * urgency_score
            + 0.05 * volunteer["reliability_score"]
            + 0.05 * task_points_norm
            - 0.03 * volunteer_aicte_norm
        )
        score = max(0.0, min(1.0, score + random.uniform(-0.05, 0.05)))

        match_success = 1 if (
            score > 0.55
            and skill_match_ratio >= 0.5
            and distance_km < 25
            and volunteer["availability_hours_week"] >= task["duration_hours"]
        ) else 0

        matches.append(
            {
                "match_id": f"M{i+1:05d}",
                "volunteer_id": volunteer["volunteer_id"],
                "task_id": task["task_id"],
                "skill_match_ratio": round(skill_match_ratio, 3),
                "willingness_score": volunteer["willingness_score"],
                "availability_hours": volunteer["availability_hours_week"],
                "distance_km": round(distance_km, 2),
                "distance_score": round(distance_score, 3),
                "fairness_score": round(fairness_score, 3),
                "urgency_level": task["urgency_level"],
                "urgency_score": round(urgency_score, 3),
                "time_compatibility": time_compatibility,
                "volunteer_reliability": volunteer["reliability_score"],  # backward compatibility
                "reliability_score": volunteer["reliability_score"],
                "task_difficulty": task["difficulty_level"],
                "ngo_reputation": task["ngo_reputation_score"],
                "volunteer_aicte_points": volunteer["aicte_points"],
                "volunteer_aicte_norm": round(volunteer_aicte_norm, 3),
                "task_points_opportunity": round(task_points_opportunity, 2),
                "task_points_possible": round(task_points_opportunity, 2),
                "task_points_norm": round(task_points_norm, 3),
                "match_score": round(score, 3),
                "match_success": match_success,
            }
        )

    return pd.DataFrame(volunteers), pd.DataFrame(tasks), pd.DataFrame(matches)


def train_and_save(output_path: str | None = None) -> str:
    df_volunteers, df_tasks, df_matches = generate_synthetic_data()

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save generated datasets for inspection/reuse.
    df_volunteers.to_csv(data_dir / "volunteers.csv", index=False)
    df_tasks.to_csv(data_dir / "tasks.csv", index=False)
    df_matches.to_csv(data_dir / "volunteer_task_matches.csv", index=False)

    feature_cols = [
        "skill_match_ratio",
        "willingness_score",
        "availability_hours",
        "distance_score",
        "fairness_score",
        "urgency_score",
        "time_compatibility",
        "reliability_score",
        "task_difficulty",
        "ngo_reputation",
        "volunteer_aicte_points",
        "volunteer_aicte_norm",
        "task_points_possible",
        "task_points_norm",
    ]
    X = df_matches[feature_cols].to_numpy(dtype=np.float32)
    y = df_matches["match_success"].to_numpy(dtype=np.int32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics: Dict[str, object] = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "positive_rate": float(np.mean(y)),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "feature_columns": feature_cols,
    }

    if output_path is None:
        output_path = str(base_dir / "random_forest.pkl")

    Path(os.path.dirname(output_path)).mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)

    with open(base_dir / "model_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Synthetic datasets saved to:", data_dir)
    print("Model saved to:", output_path)
    print("Metrics:")
    print(json.dumps(metrics, indent=2))
    return output_path


if __name__ == "__main__":
    path = train_and_save()
    print(f"Saved model to {path}")

