"""
AeroTwinX — Fault Injection Engine
===================================
Implements all 8 fault modes from the DRDO problem statement with:
  - Gradual severity ramps (simulating progressive degradation)
  - Per-cylinder fault targeting
  - Concurrent fault support (multiple faults simultaneously)
  - Proper sensor signature generation for each fault type

Fault Modes:
  1. Misfire               — Spark plug fouling / magneto drop
  2. Injector Clog         — Partial fuel injector blockage
  3. Cooling Degradation   — Baffle seal failure / fin blockage
  4. Lubrication Failure   — Oil pump wear / oil loss
  5. Sensor Drift          — Thermocouple junction oxidation
  6. Combustion Instability— Irregular ignition / detonation
  7. Overheating           — Global cooling system degradation
  8. Abnormal Vibration    — Propeller/crankshaft imbalance
"""

import time
import numpy as np


FAULT_TYPES = [
    "misfire",
    "injector_clog",
    "cooling_degradation",
    "lubrication_failure",
    "sensor_drift",
    "combustion_instability",
    "overheating",
    "abnormal_vibration",
]

FAULT_DESCRIPTIONS = {
    "misfire": "Spark plug fouling / magneto drop on cylinder {cyl}",
    "injector_clog": "Partial fuel injector blockage on cylinder {cyl}",
    "cooling_degradation": "Cooling baffle degradation on cylinder {cyl}",
    "lubrication_failure": "Oil pump wear / lubrication pressure loss",
    "sensor_drift": "CHT thermocouple drift on cylinder {cyl}",
    "combustion_instability": "Irregular combustion / detonation tendency",
    "overheating": "Global cooling system efficiency loss",
    "abnormal_vibration": "Propeller / crankshaft mass imbalance",
}


class FaultInjector:
    """Manages fault injection and progressive degradation for the engine simulator."""

    def __init__(self, engine):
        self.engine = engine
        self.active_faults = []  # List of active fault dicts
        self._fault_history = []  # All injected faults (for replay)

    def inject_fault(self, fault_type: str, severity: float = 1.0,
                     ramp_seconds: float = 60.0, cylinder: int = 2):
        """
        Inject a fault into the engine.

        Args:
            fault_type: One of FAULT_TYPES
            severity: Target severity 0.0 (none) to 1.0 (full)
            ramp_seconds: Time to reach target severity (gradual onset)
            cylinder: Affected cylinder index 0-3 (for per-cyl faults)
        """
        if fault_type not in FAULT_TYPES:
            raise ValueError(f"Unknown fault type: {fault_type}. Must be one of {FAULT_TYPES}")

        cylinder = max(0, min(3, cylinder))

        fault = {
            "type": fault_type,
            "target_severity": float(severity),
            "ramp_seconds": float(ramp_seconds),
            "cylinder": cylinder,
            "start_mission_time": self.engine.mission_time,
            "current_severity": 0.0,
            "description": FAULT_DESCRIPTIONS.get(fault_type, fault_type).format(cyl=cylinder + 1),
            "active": True,
        }
        self.active_faults.append(fault)
        self._fault_history.append(fault.copy())
        return fault

    def clear_faults(self):
        """Remove all active faults and reset engine to healthy state."""
        self.active_faults = []
        self.engine.spark_efficiency = np.ones(4)
        self.engine.injector_health = np.ones(4)
        self.engine.baffle_health = np.ones(4)
        self.engine.oil_pump_health = 1.0
        self.engine.cooling_efficiency = 1.0
        self.engine.imbalance_factor = 0.0
        self.engine.spark_jitter = 0.0
        self.engine.ring_blowby_factor = 0.0
        self.engine.sensor_drift = np.zeros(4)

    def update(self):
        """
        Update all active faults — compute current severity and apply to engine.
        Called every simulation timestep.
        """
        # First reset all fault parameters to healthy baseline
        self.engine.spark_efficiency[:] = 1.0
        self.engine.injector_health[:] = 1.0
        self.engine.baffle_health[:] = 1.0
        self.engine.oil_pump_health = 1.0
        self.engine.cooling_efficiency = 1.0
        self.engine.imbalance_factor = 0.0
        self.engine.spark_jitter = 0.0
        self.engine.ring_blowby_factor = 0.0
        self.engine.sensor_drift[:] = 0.0

        for fault in self.active_faults:
            if not fault["active"]:
                continue

            # Compute ramp progress (0→1 over ramp_seconds)
            elapsed = self.engine.mission_time - fault["start_mission_time"]
            if fault["ramp_seconds"] > 0:
                progress = min(1.0, elapsed / fault["ramp_seconds"])
                # Use sigmoid-like ramp for realistic degradation curve
                # Slow start, accelerating degradation
                progress = progress ** 1.5
            else:
                progress = 1.0

            severity = fault["target_severity"] * progress
            fault["current_severity"] = round(severity, 4)
            cyl = fault["cylinder"]

            # ─── APPLY FAULT EFFECTS ───
            ft = fault["type"]

            if ft == "misfire":
                # Spark efficiency drops on affected cylinder
                self.engine.spark_efficiency[cyl] = max(0.0, 1.0 - severity)

            elif ft == "injector_clog":
                # Injector flow reduced on affected cylinder
                self.engine.injector_health[cyl] = max(0.3, 1.0 - severity * 0.7)

            elif ft == "cooling_degradation":
                # Cooling baffle effectiveness drops on affected cylinder
                self.engine.baffle_health[cyl] = max(0.2, 1.0 - severity * 0.8)
                # Slight ring blowby from thermal stress
                self.engine.ring_blowby_factor = max(self.engine.ring_blowby_factor,
                                                      severity * 0.2)

            elif ft == "lubrication_failure":
                # Oil pump health degrades
                self.engine.oil_pump_health = max(0.3, 1.0 - severity * 0.7)
                # Blowby increases as bearings wear
                self.engine.ring_blowby_factor = max(self.engine.ring_blowby_factor,
                                                      severity * 0.4)

            elif ft == "sensor_drift":
                # Progressive bias on CHT sensor (°F drift)
                drift_amount = severity * 35.0  # Up to 35°F drift
                self.engine.sensor_drift[cyl] = drift_amount

            elif ft == "combustion_instability":
                # Random spark timing jitter
                self.engine.spark_jitter = max(self.engine.spark_jitter,
                                                severity * 0.6)

            elif ft == "overheating":
                # Global cooling reduction (all cylinders)
                self.engine.cooling_efficiency = min(self.engine.cooling_efficiency,
                                                      max(0.2, 1.0 - severity * 0.7))

            elif ft == "abnormal_vibration":
                # Propeller/crankshaft imbalance
                self.engine.imbalance_factor = max(self.engine.imbalance_factor,
                                                    severity * 3.0)

    def get_active_fault_names(self) -> list:
        """Return list of active fault type strings."""
        return [f["type"] for f in self.active_faults if f["active"] and f["current_severity"] > 0.01]

    def get_fault_summary(self) -> list:
        """Return serializable list of fault info for WebSocket."""
        return [
            {
                "type": f["type"],
                "description": f["description"],
                "severity": f["current_severity"],
                "cylinder": f["cylinder"],
                "elapsed_s": round(self.engine.mission_time - f["start_mission_time"], 1),
            }
            for f in self.active_faults
            if f["active"]
        ]
