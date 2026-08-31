"""
AeroTwinX — Synthetic Training Data Generator
===============================================
Generates labeled datasets by running the physics simulator with
various fault injections for training the fault classifier.

Each sample:
  1. Initialize engine at random operating point
  2. Run for warmup steps to reach thermal equilibrium
  3. Optionally inject a fault at random severity
  4. Run for stabilization steps
  5. Record final sensor state + label
"""

import numpy as np
import pandas as pd
from engine_simulator import EngineSimulator
from fault_injector import FaultInjector, FAULT_TYPES


def generate_dataset(num_samples_per_class: int = 200, warmup_steps: int = 50,
                     fault_steps: int = 30) -> pd.DataFrame:
    """
    Generate a balanced synthetic dataset for fault classification.

    Args:
        num_samples_per_class: Number of samples per fault class (including normal)
        warmup_steps: Steps to run before fault injection (engine warmup)
        fault_steps: Steps to run after fault injection (fault propagation)

    Returns:
        DataFrame with feature columns + 'label' column
    """
    all_classes = ["normal"] + FAULT_TYPES
    rows = []

    for fault_class in all_classes:
        for sample_idx in range(num_samples_per_class):
            engine = EngineSimulator()
            injector = FaultInjector(engine)

            # Random operating conditions
            throttle = np.random.uniform(0.4, 0.95)
            mixture = np.random.uniform(0.55, 0.90)
            altitude = np.random.uniform(0, 20000)
            tas = np.random.uniform(60, 160)
            oat = 15.0 - altitude * 0.002 + np.random.uniform(-5, 5)

            # Warmup to thermal equilibrium
            for _ in range(warmup_steps):
                engine.step(throttle=throttle, mixture=mixture,
                           tas_knots=tas, altitude_ft=altitude, oat_c=oat)

            # Inject fault (if not normal)
            if fault_class != "normal":
                severity = np.random.uniform(0.4, 1.0)
                cylinder = np.random.randint(0, 4)
                injector.inject_fault(fault_class, severity=severity,
                                     ramp_seconds=0.0, cylinder=cylinder)
                injector.update()

                # Let fault propagate
                for _ in range(fault_steps):
                    engine.step(throttle=throttle, mixture=mixture,
                               tas_knots=tas, altitude_ft=altitude, oat_c=oat)
                    injector.update()

            # Record state
            state = engine.get_state()
            row = {
                "rpm": state["rpm"],
                "map_inHg": state["map_inHg"],
                "fuel_flow_gph": state["fuel_flow_gph"],
                "cht1": state["cht"][0],
                "cht2": state["cht"][1],
                "cht3": state["cht"][2],
                "cht4": state["cht"][3],
                "egt1": state["egt"][0],
                "egt2": state["egt"][1],
                "egt3": state["egt"][2],
                "egt4": state["egt"][3],
                "oil_temp_f": state["oil_temp_f"],
                "oil_press_psi": state["oil_press_psi"],
                "vib_g_rms": state["vib_g_rms"],
                "crankcase_press": state["crankcase_press"],
                "label": fault_class,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    # Shuffle
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)

    print(f"Generated {len(df)} samples across {len(all_classes)} classes:")
    print(df["label"].value_counts().to_string())
    return df


if __name__ == "__main__":
    df = generate_dataset(num_samples_per_class=100)
    df.to_csv("training_data.csv", index=False)
    print(f"\nSaved to training_data.csv ({len(df)} rows)")
