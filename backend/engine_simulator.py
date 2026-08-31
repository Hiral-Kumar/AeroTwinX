"""
AeroTwinX — Aero Piston Engine Digital Twin Simulator
=====================================================
Physics-based 4-cylinder fuel-injected aero piston engine (Lycoming IO-360 class)
Implements:
  - Air-standard Otto cycle thermodynamics
  - Wiebe-inspired combustion heat release per cylinder
  - Lumped-parameter thermal network (CHT dynamics)
  - Oil circuit hydraulics with temperature-dependent viscosity
  - ISA standard atmosphere for altitude effects
  - Vibration synthesis with misfire/imbalance components
  - Per-cylinder fault isolation

Sensor outputs at each timestep (10 Hz):
  RPM, MAP, Fuel Flow, CHT×4, EGT×4, Oil Temp, Oil Pressure,
  Vibration g_RMS, Crankcase Pressure, Battery Voltage, Alternator Amps
"""

import numpy as np
import math


class EngineSimulator:
    """Thermodynamic 4-cylinder horizontally-opposed aero piston engine."""

    def __init__(self, dt: float = 0.1):
        self.dt = dt  # Integration timestep (seconds), 10 Hz
        self.cylinders = 4
        self.displacement_ci = 360.0  # cubic inches (IO-360)
        self.compression_ratio = 8.7
        self.J_inertia = 0.85  # kg·m² (engine + propeller)

        # Thermal capacities (J/K equivalent scaling)
        self.C_head = np.array([4500.0] * 4)  # Per-cylinder head thermal mass
        self.C_oil = 12000.0  # Oil system thermal mass

        # Cooling geometry
        self.A_fin = 0.35  # m² per cylinder fin area
        self.A_oil_cooler = 0.15  # m² oil cooler area

        # Fuel properties (100LL avgas)
        self.LHV = 43.5e6  # J/kg lower heating value
        self.fuel_density = 6.01  # lb/gal

        # ─── STATE VARIABLES ───
        self.rpm = 800.0
        self.map_inHg = 15.0
        self.cht = np.array([200.0, 200.0, 200.0, 200.0])  # °F per cylinder
        self.egt = np.array([800.0, 800.0, 800.0, 800.0])   # °F per cylinder
        self.oil_temp_f = 120.0
        self.oil_press_psi = 55.0
        self.fuel_flow_gph = 4.0
        self.vib_g_rms = 0.15
        self.crankcase_press = 1.2  # inH₂O
        self.battery_v = 28.2
        self.alternator_a = 28.0

        # Timing
        self.mission_time = 0.0

        # ─── FAULT PARAMETERS (1.0 = fully healthy) ───
        self.spark_efficiency = np.ones(4)
        self.injector_health = np.ones(4)
        self.baffle_health = np.ones(4)
        self.oil_pump_health = 1.0
        self.cooling_efficiency = 1.0
        self.imbalance_factor = 0.0  # 0 = balanced
        self.spark_jitter = 0.0
        self.ring_blowby_factor = 0.0
        self.sensor_drift = np.zeros(4)  # Per-cylinder CHT drift bias

    def reset(self):
        """Reset engine to cold start state."""
        self.__init__(self.dt)

    def isa_atmosphere(self, altitude_ft: float):
        """ISA standard atmosphere model."""
        alt_m = altitude_ft * 0.3048
        if alt_m < 11000:
            T_K = 288.15 - 0.0065 * alt_m
            P_Pa = 101325.0 * (T_K / 288.15) ** 5.2559
        else:
            T_K = 216.65
            P_Pa = 22632.0 * math.exp(-0.00015769 * (alt_m - 11000))
        rho = P_Pa / (287.05 * T_K)
        P_inHg = P_Pa / 3386.39
        return T_K, P_Pa, rho, P_inHg

    def step(self, throttle: float = 0.7, mixture: float = 0.8,
             tas_knots: float = 120.0, altitude_ft: float = 5000.0,
             oat_c: float = 15.0):
        """
        Advance engine state by one timestep.

        Args:
            throttle: 0.0 (idle) to 1.0 (full power)
            mixture: 0.0 (full lean) to 1.0 (full rich)
            tas_knots: True airspeed in knots
            altitude_ft: Pressure altitude in feet
            oat_c: Outside air temperature in °C
        """
        self.mission_time += self.dt

        # ─── 1. ATMOSPHERE & ENVIRONMENTAL CONDITIONS ───
        _, _, rho_air, p_amb_inHg = self.isa_atmosphere(altitude_ft)
        t_amb_f = oat_c * 9.0 / 5.0 + 32.0
        cooling_airspeed_fps = max(tas_knots * 1.68781, 25.0)  # ft/s, min for prop wash

        # ─── 2. MANIFOLD PRESSURE DYNAMICS ───
        # MAP responds to throttle position and ambient pressure
        target_map = p_amb_inHg * (0.30 + 0.70 * throttle)
        tau_manifold = 0.25  # seconds time constant
        self.map_inHg += (target_map - self.map_inHg) * (self.dt / tau_manifold)

        # ─── 3. VOLUMETRIC EFFICIENCY & AIR MASS FLOW ───
        vol_eff = 0.82 + 0.06 * (self.rpm / 2700.0)  # Improves with RPM up to a point
        air_mass_rate = (vol_eff * (self.rpm / 2.0) * (self.displacement_ci * 16.387e-6)
                         * rho_air / 60.0)  # kg/s

        # ─── 4. FUEL FLOW & AIR-FUEL RATIO ───
        # Mixture control: 0.0 = very lean (λ≈1.15), 1.0 = full rich (λ≈0.85)
        target_afr = 14.7 * (1.15 - 0.30 * mixture)  # Leaner at low mixture
        fuel_mass_rate = air_mass_rate / target_afr  # kg/s

        # Apply per-cylinder injector health (affects total flow)
        avg_injector_health = float(np.mean(self.injector_health))
        fuel_mass_rate *= avg_injector_health

        # Convert to GPH for display
        self.fuel_flow_gph = fuel_mass_rate * 2.20462 * 3600.0 / self.fuel_density

        # ─── 5. TORQUE BALANCE & RPM DYNAMICS ───
        # Indicated torque from combustion
        imep_bar = 8.5 * (self.map_inHg / 29.92) * np.mean(self.spark_efficiency * self.injector_health)
        indicated_torque = (imep_bar * 1e5 * self.displacement_ci * 16.387e-6) / (4.0 * math.pi)

        # Propeller load (quadratic with RPM)
        prop_torque = 2.8e-5 * self.rpm ** 2.15

        # Friction torque (temperature dependent)
        mu_factor = max(0.5, 1.5 - (self.oil_temp_f - 100.0) / 200.0)
        friction_torque = (12.0 + 0.008 * self.rpm) * mu_factor

        # Net torque → angular acceleration
        net_torque = indicated_torque - prop_torque - friction_torque
        d_omega = net_torque / self.J_inertia  # rad/s²
        d_rpm = d_omega * 30.0 / math.pi * self.dt
        self.rpm = np.clip(self.rpm + d_rpm, 600.0, 2800.0)

        # ─── 6. PER-CYLINDER COMBUSTION, EGT & CHT ───
        h_air_base = 0.042 * (cooling_airspeed_fps ** 0.78)  # W/(m²·K) scaled

        for i in range(self.cylinders):
            # --- Combustion heat release per cylinder ---
            cyl_afr = target_afr / max(self.injector_health[i], 0.3)
            cyl_lambda = cyl_afr / 14.7

            # Spark jitter effect (combustion instability)
            eff_spark = self.spark_efficiency[i] * (1.0 - self.spark_jitter * np.random.uniform(0, 1))
            eff_spark = max(0.0, min(1.0, eff_spark))

            # Wiebe-inspired combustion efficiency (peaks near stoichiometric)
            wiebe_eff = 1.0 - 0.5 * (cyl_lambda - 1.0) ** 2
            wiebe_eff = max(0.2, min(1.0, wiebe_eff))

            q_comb = (fuel_mass_rate / self.cylinders) * self.LHV * eff_spark * wiebe_eff

            # --- EGT Dynamics ---
            if eff_spark < 0.3:
                # Misfire: unburned charge → low EGT
                target_egt = t_amb_f + 200.0 + np.random.normal(0, 30)
            else:
                # EGT rises with lean mixture, peaks near stoich
                base_egt = 1250.0 + (1.0 - abs(cyl_lambda - 1.0) / 0.3) * 280.0
                target_egt = base_egt * (0.7 + 0.3 * self.rpm / 2700.0)

            tau_egt = 1.0  # EGT thermocouple time constant
            self.egt[i] += (target_egt - self.egt[i]) * (self.dt / tau_egt)
            self.egt[i] += np.random.normal(0, 2.0)  # Sensor noise

            # --- CHT Dynamics (lumped thermal balance) ---
            # Heat IN: combustion
            q_in = q_comb * 0.30  # ~30% of combustion heat goes to cylinder head

            # Heat OUT: air cooling through fins
            h_cooling = h_air_base * self.baffle_health[i] * self.cooling_efficiency
            q_air = h_cooling * self.A_fin * ((self.cht[i] - t_amb_f) * 5.0 / 9.0)  # Convert ΔT to K

            # Heat OUT: oil cooling
            q_oil = 35.0 * ((self.cht[i] - self.oil_temp_f) * 5.0 / 9.0)  # W

            # Thermal balance: C * dT/dt = Q_in - Q_out
            dT_K = (q_in - q_air - q_oil) / self.C_head[i] * self.dt
            self.cht[i] += dT_K * 9.0 / 5.0  # Convert K → °F change

            # Add sensor noise and drift
            self.cht[i] += np.random.normal(0, 0.5) + self.sensor_drift[i]

            # Clamp to physical bounds
            self.cht[i] = np.clip(self.cht[i], t_amb_f, 600.0)
            self.egt[i] = np.clip(self.egt[i], t_amb_f, 1800.0)

        # ─── 7. OIL CIRCUIT DYNAMICS ───
        # Heat IN: friction + cylinder heat transfer
        q_friction = friction_torque * self.rpm * 2.0 * math.pi / 60.0  # Watts
        q_oil_from_cyls = float(np.sum(35.0 * ((self.cht - self.oil_temp_f) * 5.0 / 9.0)))

        # Heat OUT: oil cooler (function of airspeed)
        h_oil_cooler = 25.0 * (cooling_airspeed_fps / 200.0) ** 0.6
        q_oil_cooler = h_oil_cooler * self.A_oil_cooler * ((self.oil_temp_f - t_amb_f) * 5.0 / 9.0)

        dT_oil_K = (q_friction * 0.4 + q_oil_from_cyls - q_oil_cooler) / self.C_oil * self.dt
        self.oil_temp_f += dT_oil_K * 9.0 / 5.0
        self.oil_temp_f += np.random.normal(0, 0.15)
        self.oil_temp_f = np.clip(self.oil_temp_f, t_amb_f, 280.0)

        # Oil pressure: pump output minus hydraulic losses
        pump_press = (25.0 + 55.0 * (self.rpm / 2700.0)) * self.oil_pump_health
        # Viscosity drops with temperature → pressure drops
        viscosity_factor = max(0.4, 1.3 - (self.oil_temp_f - 150.0) / 300.0)
        self.oil_press_psi = pump_press * viscosity_factor + np.random.normal(0, 0.4)
        self.oil_press_psi = max(5.0, self.oil_press_psi)

        # ─── 8. VIBRATION SYNTHESIS ───
        # Base vibration (mechanical)
        base_vib = 0.15 + 0.35 * (self.rpm / 2700.0) ** 2

        # Misfire contribution (half-order vibration)
        misfire_vib = float(np.sum(1.0 - self.spark_efficiency)) * 0.4

        # Imbalance contribution (1X RPM)
        imbalance_vib = self.imbalance_factor * 0.3 * (self.rpm / 2700.0)

        # Combustion instability contribution
        instability_vib = self.spark_jitter * 0.25 * np.random.uniform(0.5, 1.5)

        self.vib_g_rms = base_vib + misfire_vib + imbalance_vib + instability_vib
        self.vib_g_rms += np.random.normal(0, 0.02)
        self.vib_g_rms = max(0.05, self.vib_g_rms)

        # ─── 9. CRANKCASE PRESSURE ───
        self.crankcase_press = (1.0 + self.ring_blowby_factor * 5.0
                                + (self.rpm / 2700.0) * 0.8
                                + np.random.normal(0, 0.05))
        self.crankcase_press = max(0.3, self.crankcase_press)

        # ─── 10. ELECTRICAL SYSTEM ───
        self.alternator_a = 25.0 + 8.0 * (self.rpm / 2700.0) + np.random.normal(0, 0.3)
        load_draw = 22.0 + np.random.normal(0, 0.5)
        if self.alternator_a > load_draw:
            self.battery_v = min(29.0, self.battery_v + 0.001 * self.dt)
        else:
            self.battery_v = max(24.0, self.battery_v - 0.005 * self.dt)
        self.battery_v += np.random.normal(0, 0.02)

    def get_state(self) -> dict:
        """Return current engine state as a dictionary."""
        return {
            "rpm": round(float(self.rpm), 1),
            "map_inHg": round(float(self.map_inHg), 2),
            "fuel_flow_gph": round(float(self.fuel_flow_gph), 2),
            "cht": [round(float(c), 1) for c in self.cht],
            "egt": [round(float(e), 1) for e in self.egt],
            "oil_temp_f": round(float(self.oil_temp_f), 1),
            "oil_press_psi": round(float(self.oil_press_psi), 1),
            "vib_g_rms": round(float(self.vib_g_rms), 3),
            "crankcase_press": round(float(self.crankcase_press), 2),
            "battery_v": round(float(self.battery_v), 2),
            "alternator_a": round(float(self.alternator_a), 1),
        }


class PhysicsPredictor:
    """
    Baseline physics model that predicts EXPECTED sensor values
    given current operating conditions (no degradation).
    This is the 'ideal engine' — divergence from this = anomaly.
    """

    def __init__(self):
        self.C_head_nom = 4500.0
        self.A_fin = 0.35
        self._cht_pred = np.array([200.0] * 4)
        self._oil_temp_pred = 120.0

    def predict(self, rpm: float, map_inHg: float, fuel_flow_gph: float,
                tas_knots: float, altitude_ft: float, oat_c: float) -> dict:
        """Predict what a HEALTHY engine should read at these conditions."""
        t_amb_f = oat_c * 9.0 / 5.0 + 32.0
        cooling_fps = max(tas_knots * 1.68781, 25.0)

        # Load factor
        load = (rpm / 2700.0) * (map_inHg / 29.92)

        # Expected CHT (thermal equilibrium)
        h_air = 0.042 * (cooling_fps ** 0.78)
        q_comb_est = load * 12000.0  # Estimated heat input (W)
        target_cht = t_amb_f + (q_comb_est / (h_air * self.A_fin + 35.0)) * (9.0 / 5.0)
        target_cht = np.clip(target_cht, t_amb_f, 500.0)

        # Smooth prediction toward equilibrium
        for i in range(4):
            self._cht_pred[i] += (target_cht - self._cht_pred[i]) * 0.05
            self._cht_pred[i] = np.clip(self._cht_pred[i], t_amb_f, 500.0)

        # Expected EGT
        egt_pred = 1250.0 + load * 200.0

        # Expected oil temp
        target_oil = 140.0 + load * 65.0
        self._oil_temp_pred += (target_oil - self._oil_temp_pred) * 0.01

        # Expected oil pressure
        oil_press_pred = 25.0 + 55.0 * (rpm / 2700.0)

        return {
            "cht": [round(float(c), 1) for c in self._cht_pred],
            "egt": [round(egt_pred, 1)] * 4,
            "oil_temp_f": round(float(self._oil_temp_pred), 1),
            "oil_press_psi": round(oil_press_pred, 1),
        }

    def reset(self):
        self._cht_pred = np.array([200.0] * 4)
        self._oil_temp_pred = 120.0
