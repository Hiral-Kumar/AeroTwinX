"""
AeroTwinX — Residual-Based Anomaly Detector
=============================================
Computes anomaly scores by comparing ACTUAL sensor readings against
PHYSICS MODEL predictions (from PhysicsPredictor).

Method:
  1. Residual vector: r(t) = y_actual(t) - y_predicted(t)
  2. Mahalanobis distance on residuals
  3. CUSUM detector for slow drift detection
  4. Normalized anomaly score (0-100)

This is DEFENSIBLE even on synthetic data because the physics model
is grounded in thermodynamics, NOT learned from the same dataset.
"""

import numpy as np
from collections import deque


class AnomalyDetector:
    """Physics-residual anomaly detector with Mahalanobis distance."""

    def __init__(self, calibration_window: int = 200):
        self.calibration_window = calibration_window

        # Baseline statistics (computed during healthy calibration)
        self.residual_history = deque(maxlen=calibration_window)
        self.mean = None       # Baseline residual mean
        self.cov_inv = None    # Inverse covariance matrix
        self.is_calibrated = False
        self.calibration_count = 0

        # CUSUM detector state
        self.cusum_pos = 0.0
        self.cusum_neg = 0.0
        self.cusum_threshold = 8.0
        self.cusum_drift = 0.5

        # Thresholds
        self.anomaly_threshold = 3.0  # Mahalanobis distance threshold
        self.score_scale = 20.0       # Scale for 0-100 score

        # Sensor keys used for residual computation
        self.sensor_keys = ["cht0", "cht1", "cht2", "cht3",
                            "egt0", "egt1", "egt2", "egt3",
                            "oil_temp", "oil_press"]

    def compute_residuals(self, actual: dict, predicted: dict) -> dict:
        """Compute per-sensor residuals between actual and predicted."""
        residuals = {}
        for i in range(4):
            residuals[f"cht{i}"] = actual["cht"][i] - predicted["cht"][i]
            residuals[f"egt{i}"] = actual["egt"][i] - predicted["egt"][i]
        residuals["oil_temp"] = actual["oil_temp_f"] - predicted["oil_temp_f"]
        residuals["oil_press"] = actual["oil_press_psi"] - predicted["oil_press_psi"]
        return residuals

    def _residual_vector(self, residuals: dict) -> np.ndarray:
        """Convert residual dict to numpy vector."""
        return np.array([residuals.get(k, 0.0) for k in self.sensor_keys])

    def calibrate_step(self, residuals: dict):
        """Add a residual sample to the calibration window."""
        vec = self._residual_vector(residuals)
        self.residual_history.append(vec)
        self.calibration_count += 1

        if self.calibration_count >= self.calibration_window:
            self._compute_baseline()

    def _compute_baseline(self):
        """Compute baseline mean and covariance from calibration data."""
        data = np.array(list(self.residual_history))
        self.mean = np.mean(data, axis=0)
        cov = np.cov(data, rowvar=False)

        # Regularize covariance for numerical stability
        cov += np.eye(len(self.sensor_keys)) * 1.0
        try:
            self.cov_inv = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            self.cov_inv = np.eye(len(self.sensor_keys)) * 0.01
        self.is_calibrated = True

    def check_anomaly(self, actual: dict, predicted: dict) -> dict:
        """
        Check for anomalies using residual analysis.

        Returns dict with anomaly score, Mahalanobis distance,
        whether threshold is exceeded, and per-sensor residuals.
        """
        residuals = self.compute_residuals(actual, predicted)
        vec = self._residual_vector(residuals)

        # If not calibrated yet, accumulate baseline and return no-anomaly
        if not self.is_calibrated:
            self.calibrate_step(residuals)
            return {
                "score": 0.0,
                "mahalanobis_distance": 0.0,
                "threshold": self.anomaly_threshold,
                "is_anomaly": False,
                "residuals": {k: round(v, 2) for k, v in residuals.items()},
                "cusum": 0.0,
                "calibrating": True,
            }

        # Mahalanobis distance
        diff = vec - self.mean
        md_sq = float(diff @ self.cov_inv @ diff)
        md = float(np.sqrt(max(0.0, md_sq)))

        # CUSUM detector for slow drift
        self.cusum_pos = max(0, self.cusum_pos + md - self.cusum_drift)
        self.cusum_neg = max(0, self.cusum_neg - md + self.cusum_drift)

        # Anomaly determination
        is_anomaly = md > self.anomaly_threshold or self.cusum_pos > self.cusum_threshold

        # Normalized score (0-100)
        score = min(100.0, (md / self.anomaly_threshold) * self.score_scale)

        # Find top contributing sensors
        top_residuals = {}
        for k, v in residuals.items():
            top_residuals[k] = round(v, 2)

        return {
            "score": round(score, 1),
            "mahalanobis_distance": round(md, 3),
            "threshold": self.anomaly_threshold,
            "is_anomaly": bool(is_anomaly),
            "residuals": top_residuals,
            "cusum": round(self.cusum_pos, 2),
            "calibrating": False,
        }

    def reset(self):
        """Reset detector state for new mission."""
        self.residual_history.clear()
        self.mean = None
        self.cov_inv = None
        self.is_calibrated = False
        self.calibration_count = 0
        self.cusum_pos = 0.0
        self.cusum_neg = 0.0
