"""
AeroTwinX — Mission Profiles
==============================
Pre-defined MALE UAV flight mission profiles with time-series control inputs.
Each profile defines a sequence of flight segments with:
  - Time offset (seconds)
  - Throttle position (0-1)
  - Mixture setting (0-1)
  - Target altitude (feet)
  - True airspeed (knots)
  - OAT offset from ISA (°C)

Mission profiles as specified in the DRDO problem statement:
  1. ISR Patrol       — Standard surveillance mission
  2. High Altitude    — Climb to 25,000 ft, lean operations
  3. Hot Weather      — Ground-level, OAT +45°C, cooling stress
  4. Endurance        — Maximum range, economy cruise, 12 hours
  5. Rapid Throttle   — Aggressive throttle transitions, combat maneuvers
"""


def _lerp_segments(segments: list, t: float) -> dict:
    """Linearly interpolate between mission segments at time t."""
    if not segments:
        return {"throttle": 0.5, "mixture": 0.7, "altitude_ft": 5000,
                "tas_knots": 100, "oat_c": 15.0, "phase": "UNKNOWN"}

    # Find surrounding segments
    prev = segments[0]
    for seg in segments:
        if seg["t"] <= t:
            prev = seg
        else:
            break

    nxt = prev
    for seg in segments:
        if seg["t"] > t:
            nxt = seg
            break

    if nxt["t"] == prev["t"]:
        frac = 0.0
    else:
        frac = (t - prev["t"]) / (nxt["t"] - prev["t"])
        frac = max(0.0, min(1.0, frac))

    return {
        "throttle": prev["throttle"] + (nxt["throttle"] - prev["throttle"]) * frac,
        "mixture": prev["mixture"] + (nxt["mixture"] - prev["mixture"]) * frac,
        "altitude_ft": prev["altitude_ft"] + (nxt["altitude_ft"] - prev["altitude_ft"]) * frac,
        "tas_knots": prev["tas_knots"] + (nxt["tas_knots"] - prev["tas_knots"]) * frac,
        "oat_c": prev.get("oat_c", 15.0) + (nxt.get("oat_c", 15.0) - prev.get("oat_c", 15.0)) * frac,
        "phase": prev.get("phase", "CRUISE"),
    }


MISSION_PROFILES = {
    "isr_patrol": {
        "name": "ISR Patrol",
        "description": "Standard 8-hour ISR surveillance mission: climb, cruise at 15,000 ft, 3 loiter patterns, descent",
        "duration": 600,  # 10 min compressed for demo
        "segments": [
            {"t": 0,   "throttle": 0.3, "mixture": 0.9, "altitude_ft": 0,     "tas_knots": 0,   "oat_c": 20.0, "phase": "STARTUP"},
            {"t": 15,  "throttle": 0.95,"mixture": 0.85,"altitude_ft": 500,   "tas_knots": 80,  "oat_c": 20.0, "phase": "TAKEOFF"},
            {"t": 30,  "throttle": 0.85,"mixture": 0.80,"altitude_ft": 3000,  "tas_knots": 110, "oat_c": 14.0, "phase": "CLIMB"},
            {"t": 90,  "throttle": 0.80,"mixture": 0.75,"altitude_ft": 10000, "tas_knots": 120, "oat_c": 5.0,  "phase": "CLIMB"},
            {"t": 150, "throttle": 0.70,"mixture": 0.70,"altitude_ft": 15000, "tas_knots": 130, "oat_c": -5.0, "phase": "CRUISE"},
            {"t": 250, "throttle": 0.65,"mixture": 0.65,"altitude_ft": 15000, "tas_knots": 120, "oat_c": -5.0, "phase": "LOITER_1"},
            {"t": 350, "throttle": 0.70,"mixture": 0.70,"altitude_ft": 15000, "tas_knots": 130, "oat_c": -5.0, "phase": "TRANSIT"},
            {"t": 400, "throttle": 0.65,"mixture": 0.65,"altitude_ft": 15000, "tas_knots": 120, "oat_c": -5.0, "phase": "LOITER_2"},
            {"t": 480, "throttle": 0.55,"mixture": 0.75,"altitude_ft": 10000, "tas_knots": 140, "oat_c": 5.0,  "phase": "DESCENT"},
            {"t": 540, "throttle": 0.40,"mixture": 0.80,"altitude_ft": 3000,  "tas_knots": 100, "oat_c": 14.0, "phase": "APPROACH"},
            {"t": 580, "throttle": 0.25,"mixture": 0.85,"altitude_ft": 500,   "tas_knots": 75,  "oat_c": 20.0, "phase": "LANDING"},
            {"t": 600, "throttle": 0.15,"mixture": 0.90,"altitude_ft": 0,     "tas_knots": 0,   "oat_c": 20.0, "phase": "SHUTDOWN"},
        ],
    },
    "high_altitude": {
        "name": "High Altitude",
        "description": "Climb to 25,000 ft with lean mixture operations and reduced MAP",
        "duration": 480,
        "segments": [
            {"t": 0,   "throttle": 0.3, "mixture": 0.9, "altitude_ft": 0,     "tas_knots": 0,   "oat_c": 10.0, "phase": "STARTUP"},
            {"t": 20,  "throttle": 0.95,"mixture": 0.85,"altitude_ft": 500,   "tas_knots": 80,  "oat_c": 10.0, "phase": "TAKEOFF"},
            {"t": 60,  "throttle": 0.90,"mixture": 0.75,"altitude_ft": 5000,  "tas_knots": 100, "oat_c": 0.0,  "phase": "CLIMB"},
            {"t": 120, "throttle": 0.85,"mixture": 0.65,"altitude_ft": 15000, "tas_knots": 110, "oat_c": -15.0,"phase": "CLIMB"},
            {"t": 200, "throttle": 0.80,"mixture": 0.55,"altitude_ft": 25000, "tas_knots": 100, "oat_c": -35.0,"phase": "HIGH_CRUISE"},
            {"t": 350, "throttle": 0.75,"mixture": 0.55,"altitude_ft": 25000, "tas_knots": 95,  "oat_c": -35.0,"phase": "LOITER"},
            {"t": 400, "throttle": 0.50,"mixture": 0.70,"altitude_ft": 10000, "tas_knots": 130, "oat_c": -5.0, "phase": "DESCENT"},
            {"t": 460, "throttle": 0.30,"mixture": 0.85,"altitude_ft": 500,   "tas_knots": 75,  "oat_c": 10.0, "phase": "APPROACH"},
            {"t": 480, "throttle": 0.15,"mixture": 0.90,"altitude_ft": 0,     "tas_knots": 0,   "oat_c": 10.0, "phase": "SHUTDOWN"},
        ],
    },
    "hot_weather": {
        "name": "Hot Weather Operations",
        "description": "Ground-level operations in +45°C desert conditions — cooling stress test",
        "duration": 420,
        "segments": [
            {"t": 0,   "throttle": 0.3, "mixture": 0.95,"altitude_ft": 0,    "tas_knots": 0,   "oat_c": 45.0, "phase": "STARTUP"},
            {"t": 20,  "throttle": 0.90,"mixture": 0.90,"altitude_ft": 500,  "tas_knots": 70,  "oat_c": 44.0, "phase": "TAKEOFF"},
            {"t": 60,  "throttle": 0.80,"mixture": 0.85,"altitude_ft": 3000, "tas_knots": 100, "oat_c": 40.0, "phase": "CLIMB"},
            {"t": 120, "throttle": 0.75,"mixture": 0.80,"altitude_ft": 5000, "tas_knots": 110, "oat_c": 35.0, "phase": "CRUISE"},
            {"t": 300, "throttle": 0.70,"mixture": 0.80,"altitude_ft": 5000, "tas_knots": 105, "oat_c": 36.0, "phase": "LOITER"},
            {"t": 370, "throttle": 0.40,"mixture": 0.85,"altitude_ft": 1000, "tas_knots": 80,  "oat_c": 43.0, "phase": "APPROACH"},
            {"t": 420, "throttle": 0.15,"mixture": 0.95,"altitude_ft": 0,    "tas_knots": 0,   "oat_c": 45.0, "phase": "SHUTDOWN"},
        ],
    },
    "endurance": {
        "name": "Endurance Mission",
        "description": "Maximum endurance: lean cruise for extended duration — thermal soak test",
        "duration": 720,
        "segments": [
            {"t": 0,   "throttle": 0.3, "mixture": 0.9, "altitude_ft": 0,     "tas_knots": 0,   "oat_c": 15.0, "phase": "STARTUP"},
            {"t": 20,  "throttle": 0.90,"mixture": 0.85,"altitude_ft": 500,   "tas_knots": 80,  "oat_c": 15.0, "phase": "TAKEOFF"},
            {"t": 80,  "throttle": 0.75,"mixture": 0.70,"altitude_ft": 8000,  "tas_knots": 110, "oat_c": 1.0,  "phase": "CLIMB"},
            {"t": 150, "throttle": 0.60,"mixture": 0.55,"altitude_ft": 12000, "tas_knots": 100, "oat_c": -9.0, "phase": "ECON_CRUISE"},
            {"t": 600, "throttle": 0.60,"mixture": 0.55,"altitude_ft": 12000, "tas_knots": 100, "oat_c": -9.0, "phase": "ECON_CRUISE"},
            {"t": 660, "throttle": 0.45,"mixture": 0.75,"altitude_ft": 5000,  "tas_knots": 120, "oat_c": 5.0,  "phase": "DESCENT"},
            {"t": 700, "throttle": 0.30,"mixture": 0.85,"altitude_ft": 500,   "tas_knots": 75,  "oat_c": 15.0, "phase": "APPROACH"},
            {"t": 720, "throttle": 0.15,"mixture": 0.90,"altitude_ft": 0,     "tas_knots": 0,   "oat_c": 15.0, "phase": "SHUTDOWN"},
        ],
    },
    "rapid_throttle": {
        "name": "Rapid Throttle Transitions",
        "description": "Aggressive throttle changes — stress testing engine response and thermal cycling",
        "duration": 360,
        "segments": [
            {"t": 0,   "throttle": 0.3, "mixture": 0.85,"altitude_ft": 0,    "tas_knots": 0,   "oat_c": 20.0, "phase": "STARTUP"},
            {"t": 15,  "throttle": 0.95,"mixture": 0.85,"altitude_ft": 500,  "tas_knots": 80,  "oat_c": 20.0, "phase": "TAKEOFF"},
            {"t": 40,  "throttle": 0.90,"mixture": 0.80,"altitude_ft": 3000, "tas_knots": 130, "oat_c": 14.0, "phase": "CLIMB"},
            {"t": 80,  "throttle": 0.95,"mixture": 0.80,"altitude_ft": 5000, "tas_knots": 160, "oat_c": 10.0, "phase": "DASH"},
            {"t": 110, "throttle": 0.40,"mixture": 0.75,"altitude_ft": 5000, "tas_knots": 90,  "oat_c": 10.0, "phase": "IDLE_DESCENT"},
            {"t": 140, "throttle": 0.95,"mixture": 0.85,"altitude_ft": 5000, "tas_knots": 155, "oat_c": 10.0, "phase": "DASH"},
            {"t": 170, "throttle": 0.35,"mixture": 0.75,"altitude_ft": 4000, "tas_knots": 85,  "oat_c": 12.0, "phase": "IDLE_DESCENT"},
            {"t": 200, "throttle": 0.90,"mixture": 0.80,"altitude_ft": 6000, "tas_knots": 150, "oat_c": 8.0,  "phase": "DASH"},
            {"t": 250, "throttle": 0.70,"mixture": 0.70,"altitude_ft": 6000, "tas_knots": 120, "oat_c": 8.0,  "phase": "CRUISE"},
            {"t": 320, "throttle": 0.40,"mixture": 0.80,"altitude_ft": 1000, "tas_knots": 90,  "oat_c": 18.0, "phase": "APPROACH"},
            {"t": 360, "throttle": 0.15,"mixture": 0.90,"altitude_ft": 0,    "tas_knots": 0,   "oat_c": 20.0, "phase": "SHUTDOWN"},
        ],
    },
}


def get_missions() -> dict:
    """Return all mission profiles metadata (for API listing)."""
    return {
        mid: {
            "id": mid,
            "name": m["name"],
            "description": m["description"],
            "duration": m["duration"],
        }
        for mid, m in MISSION_PROFILES.items()
    }


def get_mission_inputs(mission_id: str, t: float) -> dict:
    """Get interpolated control inputs for a mission at time t."""
    profile = MISSION_PROFILES.get(mission_id)
    if not profile:
        # Default cruise if mission not found
        return {"throttle": 0.7, "mixture": 0.7, "altitude_ft": 5000,
                "tas_knots": 120, "oat_c": 15.0, "phase": "CRUISE"}
    return _lerp_segments(profile["segments"], t)


def get_mission_duration(mission_id: str) -> float:
    """Get total duration of a mission in seconds."""
    profile = MISSION_PROFILES.get(mission_id)
    return profile["duration"] if profile else 600.0
