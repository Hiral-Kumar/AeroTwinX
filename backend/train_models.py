"""
AeroTwinX — Model Training Script
====================================
Generates synthetic data and trains the RandomForest fault classifier.
Run once before starting the server:
    python train_models.py
"""

import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from data_generator import generate_dataset


FEATURE_COLS = [
    "rpm", "map_inHg", "fuel_flow_gph",
    "cht1", "cht2", "cht3", "cht4",
    "egt1", "egt2", "egt3", "egt4",
    "oil_temp_f", "oil_press_psi", "vib_g_rms", "crankcase_press",
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model.joblib")


def train():
    print("=" * 60)
    print("  AeroTwinX — Fault Classifier Training")
    print("=" * 60)

    # Generate synthetic dataset
    print("\n[1/3] Generating synthetic training data...")
    df = generate_dataset(num_samples_per_class=150, warmup_steps=40, fault_steps=25)

    X = df[FEATURE_COLS].values
    y = df["label"].values

    # Train RandomForest
    print("\n[2/3] Training RandomForestClassifier...")
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    # Cross-validation
    scores = cross_val_score(clf, X, y, cv=5, scoring="accuracy")
    print(f"  Cross-validation accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

    # Final fit on all data
    clf.fit(X, y)

    # Feature importance report
    print("\n  Feature Importances:")
    importances = clf.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    for i in sorted_idx[:10]:
        print(f"    {FEATURE_COLS[i]:20s} : {importances[i]:.4f}")

    # Save model
    print(f"\n[3/3] Saving model to {MODEL_PATH}")
    joblib.dump(clf, MODEL_PATH)

    print("\n[SUCCESS] Training complete!")
    print(f"  Model classes: {list(clf.classes_)}")
    print(f"  Model saved: {MODEL_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    train()
