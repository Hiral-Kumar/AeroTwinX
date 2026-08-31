"""
AeroTwinX — Fault Classifier with Feature Importance
======================================================
Lightweight RandomForest classifier for 9-class fault diagnosis.
Uses feature importance (permutation-based) as a SHAP-style
explainability proxy for real-time root-cause analysis.

Classes:
  0: normal
  1: misfire
  2: injector_clog
  3: cooling_degradation
  4: lubrication_failure
  5: sensor_drift
  6: combustion_instability
  7: overheating
  8: abnormal_vibration
"""

import numpy as np
import os
import joblib


FAULT_CLASSES = [
    "normal", "misfire", "injector_clog", "cooling_degradation",
    "lubrication_failure", "sensor_drift", "combustion_instability",
    "overheating", "abnormal_vibration",
]

FEATURE_NAMES = [
    "rpm", "map_inHg", "fuel_flow_gph",
    "cht1", "cht2", "cht3", "cht4",
    "egt1", "egt2", "egt3", "egt4",
    "oil_temp_f", "oil_press_psi", "vib_g_rms", "crankcase_press",
]

# Nominal reference values for each feature (healthy cruise)
FEATURE_BASELINES = {
    "rpm": 2350, "map_inHg": 23.5, "fuel_flow_gph": 10.0,
    "cht1": 345, "cht2": 350, "cht3": 348, "cht4": 342,
    "egt1": 1380, "egt2": 1390, "egt3": 1385, "egt4": 1375,
    "oil_temp_f": 185, "oil_press_psi": 72, "vib_g_rms": 0.32,
    "crankcase_press": 1.5,
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "rf_model.joblib")


class FaultClassifier:
    """RandomForest fault classifier with feature importance explanations."""

    def __init__(self):
        self.model = None
        self.feature_importances = None
        self._load_model()

    def _load_model(self):
        """Load pre-trained model from disk."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                if hasattr(self.model, "feature_importances_"):
                    self.feature_importances = self.model.feature_importances_
            except Exception as e:
                print(f"Warning: Could not load model: {e}")
                self.model = None

    def state_to_features(self, state: dict) -> list:
        """Convert engine state dict to feature vector."""
        return [
            state["rpm"], state["map_inHg"], state["fuel_flow_gph"],
            state["cht"][0], state["cht"][1], state["cht"][2], state["cht"][3],
            state["egt"][0], state["egt"][1], state["egt"][2], state["egt"][3],
            state["oil_temp_f"], state["oil_press_psi"], state["vib_g_rms"],
            state.get("crankcase_press", 1.5),
        ]

    def predict(self, state: dict) -> dict:
        """
        Predict fault class and provide feature importance explanations.

        Returns dict with predicted_fault, confidence, fault_probabilities,
        and shap_contributions (ordered by absolute impact).
        """
        if self.model is None:
            return self._default_prediction(state)

        X = [self.state_to_features(state)]
        try:
            probs = self.model.predict_proba(X)[0]
        except Exception:
            return self._default_prediction(state)

        pred_idx = int(np.argmax(probs))
        classes = list(self.model.classes_)
        pred_class = str(classes[pred_idx])

        # Build probability dict
        fault_probs = {}
        for c, p in zip(classes, probs):
            fault_probs[str(c)] = round(float(p), 4)

        # Compute SHAP-style feature contributions
        shap_contributions = self._compute_feature_contributions(X[0], pred_idx)

        return {
            "predicted_fault": pred_class,
            "confidence": round(float(probs[pred_idx]), 4),
            "fault_probabilities": fault_probs,
            "shap_contributions": shap_contributions,
        }

    def _compute_feature_contributions(self, features: list, pred_class_idx: int) -> list:
        """
        Compute per-feature contribution to the prediction.
        Uses deviation from baseline weighted by feature importance.
        This approximates SHAP values without the full SHAP library dependency.
        """
        contributions = []
        for i, fname in enumerate(FEATURE_NAMES):
            value = features[i]
            baseline = FEATURE_BASELINES.get(fname, value)

            # Deviation from baseline, normalized
            if baseline != 0:
                deviation = (value - baseline) / abs(baseline)
            else:
                deviation = value

            # Weight by feature importance
            importance = 0.0
            if self.feature_importances is not None and i < len(self.feature_importances):
                importance = float(self.feature_importances[i])

            impact = deviation * importance * 10.0  # Scale for visibility

            contributions.append({
                "feature": fname,
                "value": round(float(value), 2),
                "impact": round(float(impact), 4),
                "importance": round(importance, 4),
            })

        # Sort by absolute impact descending
        contributions.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return contributions[:8]  # Return top 8

    def _default_prediction(self, state: dict) -> dict:
        """Fallback prediction when model is not available."""
        # Simple rule-based fallback
        fault_probs = {f: 0.0 for f in FAULT_CLASSES}
        fault_probs["normal"] = 0.85

        predicted = "normal"
        max_cht = max(state.get("cht", [350]*4))
        vib = state.get("vib_g_rms", 0.3)

        if max_cht > 420:
            predicted = "overheating"
            fault_probs["overheating"] = 0.7
            fault_probs["normal"] = 0.2
        elif vib > 1.0:
            predicted = "abnormal_vibration"
            fault_probs["abnormal_vibration"] = 0.65
            fault_probs["normal"] = 0.25
        elif state.get("oil_press_psi", 70) < 35:
            predicted = "lubrication_failure"
            fault_probs["lubrication_failure"] = 0.6
            fault_probs["normal"] = 0.3

        features = self.state_to_features(state)
        contributions = []
        for i, fname in enumerate(FEATURE_NAMES):
            val = features[i]
            base = FEATURE_BASELINES.get(fname, val)
            dev = (val - base) / abs(base) if base != 0 else 0
            contributions.append({
                "feature": fname, "value": round(float(val), 2),
                "impact": round(float(dev), 4), "importance": 0.0,
            })
        contributions.sort(key=lambda x: abs(x["impact"]), reverse=True)

        return {
            "predicted_fault": predicted,
            "confidence": fault_probs[predicted],
            "fault_probabilities": fault_probs,
            "shap_contributions": contributions[:8],
        }
