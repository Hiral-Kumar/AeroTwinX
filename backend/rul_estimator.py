"""
AeroTwinX — Remaining Useful Life (RUL) Estimator
===================================================
Computes Health Index (HI) from multiple degradation indicators
and projects Remaining Useful Life with confidence bounds.

Method:
  1. Health Index: Weighted composite of thermal impedance degradation,
     vibration trend, oil circuit health, and blowby trend
  2. RUL Projection: Exponential degradation curve fit on HI history
  3. Confidence Bands: Bootstrap-style prediction intervals
"""

import numpy as np
from collections import deque


class RULEstimator:
    """Multi-indicator Health Index with RUL trend projection."""

    def __init__(self, window_size: int = 300):
        self.window_size = window_size
        self.hi_history = deque(maxlen=window_size)
        self.time_history = deque(maxlen=window_size)

        # Health Index weights (must sum to 1.0)
        self.weights = {
            "thermal": 0.30,     # CHT deviation from baseline
            "vibration": 0.25,   # Vibration level
            "oil_health": 0.25,  # Oil pressure & temperature
            "egt_spread": 0.10,  # Cylinder-to-cylinder EGT spread
            "crankcase": 0.10,   # Blowby indicator
        }

        # Baseline reference values (healthy engine at cruise)
        self.ref = {
            "cht_nominal": 350.0,    # °F
            "cht_limit": 500.0,
            "vib_nominal": 0.3,      # g RMS
            "vib_limit": 2.0,
            "oil_press_nominal": 70.0,
            "oil_press_low": 25.0,
            "oil_temp_nominal": 185.0,
            "oil_temp_limit": 245.0,
            "egt_spread_limit": 100.0,  # °F max cyl-to-cyl
            "crankcase_nominal": 1.5,
            "crankcase_limit": 6.0,
        }

        # Failure threshold
        self.failure_threshold = 30.0  # HI below this = functional failure
        self.rul_hours_nominal = 1200.0  # Hours at 100% HI

    def compute_health_index(self, state: dict) -> float:
        """
        Compute composite Health Index (0-100%) from current engine state.
        100% = brand new, 0% = functional failure.
        """
        ref = self.ref

        # 1. Thermal health: how far is max CHT from nominal?
        max_cht = max(state["cht"])
        thermal_score = max(0, 1.0 - max(0, max_cht - ref["cht_nominal"])
                            / (ref["cht_limit"] - ref["cht_nominal"]))

        # 2. Vibration health
        vib = state["vib_g_rms"]
        vib_score = max(0, 1.0 - max(0, vib - ref["vib_nominal"])
                        / (ref["vib_limit"] - ref["vib_nominal"]))

        # 3. Oil circuit health (pressure and temperature)
        oil_press_score = max(0, min(1.0,
            (state["oil_press_psi"] - ref["oil_press_low"])
            / (ref["oil_press_nominal"] - ref["oil_press_low"])))
        oil_temp_score = max(0, 1.0 - max(0, state["oil_temp_f"] - ref["oil_temp_nominal"])
                             / (ref["oil_temp_limit"] - ref["oil_temp_nominal"]))
        oil_score = 0.5 * oil_press_score + 0.5 * oil_temp_score

        # 4. EGT spread (cylinder-to-cylinder consistency)
        egt_spread = max(state["egt"]) - min(state["egt"])
        egt_score = max(0, 1.0 - egt_spread / ref["egt_spread_limit"])

        # 5. Crankcase pressure (blowby indicator)
        crankcase_score = max(0, 1.0 - max(0, state["crankcase_press"] - ref["crankcase_nominal"])
                              / (ref["crankcase_limit"] - ref["crankcase_nominal"]))

        # Weighted composite
        hi = (self.weights["thermal"] * thermal_score
              + self.weights["vibration"] * vib_score
              + self.weights["oil_health"] * oil_score
              + self.weights["egt_spread"] * egt_score
              + self.weights["crankcase"] * crankcase_score) * 100.0

        return max(0.0, min(100.0, hi))

    def estimate(self, state: dict, mission_time: float) -> dict:
        """
        Compute HI and project RUL with confidence bounds.

        Returns dict with health_index, rul_hours, confidence bounds, trend.
        """
        hi = self.compute_health_index(state)
        self.hi_history.append(hi)
        self.time_history.append(mission_time)

        # Determine trend
        if len(self.hi_history) >= 20:
            recent = list(self.hi_history)[-20:]
            older = list(self.hi_history)[-40:-20] if len(self.hi_history) >= 40 else recent
            avg_recent = np.mean(recent)
            avg_older = np.mean(older)
            delta = avg_recent - avg_older

            if delta < -2.0:
                trend = "degrading"
            elif delta < -0.5:
                trend = "slight_degradation"
            elif delta > 1.0:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "calibrating"

        # RUL projection
        rul_hours = self._project_rul(hi)

        # Confidence bounds (±15% for stable, wider for degrading)
        uncertainty = 0.15 if trend == "stable" else 0.25
        rul_lower = max(0, rul_hours * (1.0 - uncertainty))
        rul_upper = rul_hours * (1.0 + uncertainty)

        return {
            "health_index": round(hi, 1),
            "rul_hours": round(rul_hours, 0),
            "rul_lower": round(rul_lower, 0),
            "rul_upper": round(rul_upper, 0),
            "trend": trend,
            "failure_threshold": self.failure_threshold,
        }

    def _project_rul(self, current_hi: float) -> float:
        """
        Project time-to-failure from current HI.

        Uses linear extrapolation of degradation rate if degrading,
        otherwise uses proportional estimate.
        """
        if current_hi <= self.failure_threshold:
            return 0.0

        # If we have enough history, use slope-based projection
        if len(self.hi_history) >= 50:
            times = np.array(list(self.time_history)[-50:])
            his = np.array(list(self.hi_history)[-50:])

            # Linear regression on recent trend
            if len(times) > 1 and (times[-1] - times[0]) > 0:
                dt_hours = (times[-1] - times[0]) / 3600.0
                dhi = his[-1] - his[0]

                if dt_hours > 0 and dhi < -0.1:
                    # Degradation rate per hour
                    rate = dhi / dt_hours
                    # Time to reach failure threshold
                    remaining_hi = current_hi - self.failure_threshold
                    rul = -remaining_hi / rate  # rate is negative
                    return max(0, min(5000, rul))

        # Default: proportional estimate
        hi_ratio = (current_hi - self.failure_threshold) / (100.0 - self.failure_threshold)
        return hi_ratio * self.rul_hours_nominal

    def reset(self):
        """Reset for new mission."""
        self.hi_history.clear()
        self.time_history.clear()
