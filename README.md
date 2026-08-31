# AeroTwinX

**AI-Enabled Real-Time Digital Twin System for Aero Piston Engines**
*Prototype for SIH 26054 (MALE UAVs)*

AeroTwinX is a physics-informed digital twin designed to monitor, predict, and explain faults in aero piston engines. It combines a real-time thermodynamic simulation (Otto cycle, Wiebe combustion, lumped thermal networks) with machine learning for anomaly detection and Root Cause Analysis (RCA).

## Features
- **Physics-Based Simulation**: Real-time 4-cylinder engine model (Lycoming IO-360 class).
- **Residual-Based Anomaly Detection**: Compares actual telemetry against physics predictions using Mahalanobis distance to detect degradation *before* thresholds are breached.
- **RCA via SHAP**: Explains exactly *which* sensor is contributing to a fault diagnosis.
- **Health Index & RUL**: Multi-indicator health index with Remaining Useful Life projection.
- **Adversarial Testing**: Inject 8 different DRDO-specified fault modes (Misfire, Injector Clog, Sensor Drift, etc.) on the fly.
- **Military-Grade Dashboard**: React + Three.js 3D engine visualization and real-time Canvas charts.

## Setup Instructions

### 1. Backend (Python)
The backend runs the physics simulator and the FastAPI server.
```bash
cd backend
pip install -r requirements.txt

# First-time only: generate synthetic data and train the AI model
python train_models.py

# Start the server (runs on http://localhost:8000)
uvicorn main:app --reload
```

### 2. Frontend (React/Vite)
The frontend connects to the backend via WebSocket (`ws://localhost:8000/ws/telemetry`).
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## Using the Dashboard
1. Select a **Mission Profile** from the sidebar (e.g. "ISR Patrol").
2. Click **Start** to begin the simulation. You will see the 3D engine begin to rotate and the gauges/charts populate.
3. Observe the **Telemetry Charts**. The solid lines are actual readings; the *dashed lines* are the physics predictions. When healthy, they overlap perfectly.
4. Under **Adversarial Testing**, select a fault (e.g. "Fuel Injector Clog (Cyl 3)").
5. Watch the anomaly score rise as the actual readings diverge from the physics predictions.
6. The AI will eventually classify the fault, and the **SHAP Waterfall** will explain why (e.g. "CHT3 and EGT3 dropped").
