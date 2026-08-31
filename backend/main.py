"""
AeroTwinX — FastAPI Backend Server
=====================================
Real-time Digital Twin server with:
  - WebSocket telemetry streaming at 10 Hz
  - REST API for mission control, fault injection, configuration
  - Background simulation loop (async)
  - Physics predictor for anomaly detection
  - Full integration of all modules

Usage:
    python train_models.py   # First time only
    python main.py           # Start server on port 8000
"""

import asyncio
import json
import time
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engine_simulator import EngineSimulator, PhysicsPredictor
from fault_injector import FaultInjector, FAULT_TYPES
from mission_profiles import get_missions, get_mission_inputs, get_mission_duration, MISSION_PROFILES
from anomaly_detector import AnomalyDetector
from rul_estimator import RULEstimator
from fault_classifier import FaultClassifier

# ─── APP SETUP ───
app = FastAPI(
    title="AeroTwinX Digital Twin API",
    description="AI-Enabled Real-Time Digital Twin for Aero Piston Engines",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── GLOBAL STATE ───
engine = EngineSimulator()
physics_predictor = PhysicsPredictor()
fault_injector = FaultInjector(engine)
anomaly_detector = AnomalyDetector()
rul_estimator = RULEstimator()
fault_classifier = FaultClassifier()

# Simulation state
sim_state = {
    "running": False,
    "speed": 1.0,
    "mission_id": None,
    "mission_name": None,
    "mission_duration": 0.0,
    "paused": False,
}

# Connected WebSocket clients
ws_clients: list[WebSocket] = []

# Latest telemetry frame (for REST API access)
latest_frame: dict = {}


# ─── REQUEST MODELS ───
class MissionStartRequest(BaseModel):
    mission_id: str
    fault_scenario: Optional[str] = None


class FaultInjectRequest(BaseModel):
    fault_type: str
    cylinder: int = 2
    severity: float = 0.8
    ramp_seconds: float = 60.0


class SpeedRequest(BaseModel):
    speed: float


# ─── REST API ENDPOINTS ───
@app.get("/")
def root():
    return {
        "name": "AeroTwinX Digital Twin API",
        "version": "1.0.0",
        "status": "running" if sim_state["running"] else "idle",
        "websocket": "ws://localhost:8000/ws/telemetry",
    }


@app.get("/api/missions")
def list_missions():
    """List all available mission profiles."""
    return get_missions()


@app.post("/api/mission/start")
def start_mission(req: MissionStartRequest):
    """Start a new mission simulation."""
    global engine, physics_predictor, fault_injector, anomaly_detector, rul_estimator

    if req.mission_id not in MISSION_PROFILES:
        return {"error": f"Unknown mission: {req.mission_id}",
                "available": list(MISSION_PROFILES.keys())}

    # Reset all systems
    engine = EngineSimulator()
    physics_predictor = PhysicsPredictor()
    fault_injector = FaultInjector(engine)
    anomaly_detector = AnomalyDetector()
    rul_estimator = RULEstimator()

    profile = MISSION_PROFILES[req.mission_id]
    sim_state["running"] = True
    sim_state["paused"] = False
    sim_state["mission_id"] = req.mission_id
    sim_state["mission_name"] = profile["name"]
    sim_state["mission_duration"] = profile["duration"]

    # Auto-inject fault scenario if requested
    if req.fault_scenario and req.fault_scenario in FAULT_TYPES:
        # Schedule fault injection after 30% of mission (post-calibration)
        delay = profile["duration"] * 0.3
        asyncio.get_event_loop().call_later(
            delay / max(sim_state["speed"], 0.1),
            lambda: fault_injector.inject_fault(
                req.fault_scenario, severity=0.8,
                ramp_seconds=profile["duration"] * 0.2, cylinder=2
            )
        )

    return {
        "status": "started",
        "mission": req.mission_id,
        "name": profile["name"],
        "duration": profile["duration"],
    }


@app.post("/api/mission/stop")
def stop_mission():
    """Stop current simulation."""
    sim_state["running"] = False
    sim_state["paused"] = False
    return {"status": "stopped"}


@app.post("/api/mission/pause")
def pause_mission():
    """Pause/unpause simulation."""
    sim_state["paused"] = not sim_state["paused"]
    return {"paused": sim_state["paused"]}


@app.post("/api/fault/inject")
def inject_fault(req: FaultInjectRequest):
    """Inject a fault during runtime."""
    if req.fault_type not in FAULT_TYPES:
        return {"error": f"Unknown fault type: {req.fault_type}",
                "available": FAULT_TYPES}

    fault = fault_injector.inject_fault(
        fault_type=req.fault_type,
        severity=req.severity,
        ramp_seconds=req.ramp_seconds,
        cylinder=req.cylinder,
    )
    return {"status": "fault_injected", "fault": fault["description"]}


@app.post("/api/fault/clear")
def clear_faults():
    """Clear all active faults."""
    fault_injector.clear_faults()
    return {"status": "faults_cleared"}


@app.get("/api/fault/types")
def list_fault_types():
    """List available fault types."""
    return {"fault_types": FAULT_TYPES}


@app.post("/api/simulation/speed")
def set_speed(req: SpeedRequest):
    """Set simulation speed multiplier."""
    sim_state["speed"] = max(0.25, min(16.0, req.speed))
    return {"speed": sim_state["speed"]}


@app.get("/api/status")
def get_status():
    """Get current simulation status."""
    return {
        **sim_state,
        "mission_time": engine.mission_time,
        "active_faults": fault_injector.get_fault_summary(),
        "latest_frame": latest_frame,
    }


# ─── SIMULATION LOOP ───
async def simulation_loop():
    """Background simulation loop running at ~10 Hz."""
    global latest_frame

    while True:
        if sim_state["running"] and not sim_state["paused"]:
            dt = 0.1 * sim_state["speed"]

            # Get mission control inputs
            mission_id = sim_state["mission_id"] or "isr_patrol"
            inputs = get_mission_inputs(mission_id, engine.mission_time)

            # Step the engine
            engine.step(
                throttle=inputs["throttle"],
                mixture=inputs["mixture"],
                tas_knots=inputs["tas_knots"],
                altitude_ft=inputs["altitude_ft"],
                oat_c=inputs["oat_c"],
            )

            # Update faults
            fault_injector.update()

            # Get sensor readings
            state = engine.get_state()

            # Physics baseline prediction
            prediction = physics_predictor.predict(
                rpm=state["rpm"],
                map_inHg=state["map_inHg"],
                fuel_flow_gph=state["fuel_flow_gph"],
                tas_knots=inputs["tas_knots"],
                altitude_ft=inputs["altitude_ft"],
                oat_c=inputs["oat_c"],
            )

            # Anomaly detection
            anomaly = anomaly_detector.check_anomaly(state, prediction)

            # Health & RUL estimation
            health = rul_estimator.estimate(state, engine.mission_time)

            # Fault classification
            diagnosis = fault_classifier.predict(state)

            # Check for mission completion
            duration = get_mission_duration(mission_id)
            if engine.mission_time >= duration:
                sim_state["running"] = False

            # Build telemetry frame
            frame = {
                "timestamp": time.time(),
                "mission_time": round(engine.mission_time, 2),
                "mission_phase": inputs.get("phase", "CRUISE"),
                "mission_progress": round(min(1.0, engine.mission_time / max(1, duration)), 3),
                "engine": state,
                "physics_prediction": prediction,
                "anomaly": anomaly,
                "health": health,
                "fault_diagnosis": diagnosis,
                "active_faults": fault_injector.get_fault_summary(),
                "simulation_speed": sim_state["speed"],
                "flight_conditions": {
                    "throttle": round(inputs["throttle"], 3),
                    "mixture": round(inputs["mixture"], 3),
                    "altitude_ft": round(inputs["altitude_ft"], 0),
                    "tas_knots": round(inputs["tas_knots"], 1),
                    "oat_c": round(inputs["oat_c"], 1),
                },
            }
            latest_frame = frame

            # Broadcast to all WebSocket clients
            frame_json = json.dumps(frame)
            disconnected = []
            for ws in ws_clients:
                try:
                    await ws.send_text(frame_json)
                except Exception:
                    disconnected.append(ws)

            for ws in disconnected:
                ws_clients.remove(ws)

        await asyncio.sleep(0.1 / max(sim_state["speed"], 0.25))


@app.on_event("startup")
async def startup():
    """Start the simulation loop on server startup."""
    asyncio.create_task(simulation_loop())
    print("\n" + "=" * 60)
    print("  AeroTwinX Digital Twin Server")
    print("  WebSocket: ws://localhost:8000/ws/telemetry")
    print("  REST API:  http://localhost:8000/docs")
    print("=" * 60 + "\n")


# ─── WEBSOCKET ENDPOINT ───
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming."""
    await websocket.accept()
    ws_clients.append(websocket)
    print(f"[WS] Client connected. Total clients: {len(ws_clients)}")

    try:
        while True:
            # Listen for control messages from the client
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)

                # Handle client commands
                if msg.get("type") == "start_mission":
                    start_mission(MissionStartRequest(
                        mission_id=msg.get("mission_id", "isr_patrol"),
                        fault_scenario=msg.get("fault_scenario"),
                    ))
                elif msg.get("type") == "inject_fault":
                    inject_fault(FaultInjectRequest(
                        fault_type=msg.get("fault_type", "misfire"),
                        cylinder=msg.get("cylinder", 2),
                        severity=msg.get("severity", 0.8),
                        ramp_seconds=msg.get("ramp_seconds", 60.0),
                    ))
                elif msg.get("type") == "set_speed":
                    set_speed(SpeedRequest(speed=msg.get("speed", 1.0)))
                elif msg.get("type") == "stop":
                    stop_mission()

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        if websocket in ws_clients:
            ws_clients.remove(websocket)
        print(f"[WS] Client disconnected. Total clients: {len(ws_clients)}")


# ─── MAIN ENTRY ───
if __name__ == "__main__":
    import uvicorn

    # Check if model exists, suggest training if not
    if not os.path.exists("rf_model.joblib"):
        print("\n⚠ No trained model found. Run 'python train_models.py' first.")
        print("  Starting server anyway (will use rule-based fallback)...\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
