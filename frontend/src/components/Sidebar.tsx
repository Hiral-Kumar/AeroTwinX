import React, { useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';

const API_BASE = 'http://localhost:8000';

const MISSIONS = [
  { id: 'isr_patrol', name: 'ISR Patrol (10 min)' },
  { id: 'high_altitude', name: 'High Altitude (8 min)' },
  { id: 'hot_weather', name: 'Hot Weather (7 min)' },
  { id: 'endurance', name: 'Endurance (12 min)' },
  { id: 'rapid_throttle', name: 'Rapid Throttle (6 min)' },
];

const FAULT_TYPES = [
  { id: 'misfire', name: 'Spark Plug Misfire (Cyl 3)', cyl: 2 },
  { id: 'injector_clog', name: 'Fuel Injector Clog (Cyl 3)', cyl: 2 },
  { id: 'cooling_degradation', name: 'Cooling Baffle Failure (Cyl 3)', cyl: 2 },
  { id: 'lubrication_failure', name: 'Oil Pump Degradation', cyl: 0 },
  { id: 'sensor_drift', name: 'CHT Sensor Drift (Cyl 2)', cyl: 1 },
  { id: 'combustion_instability', name: 'Combustion Instability', cyl: 0 },
  { id: 'overheating', name: 'Global Overheating', cyl: 0 },
  { id: 'abnormal_vibration', name: 'Propeller Imbalance', cyl: 0 },
];

export const Sidebar: React.FC = () => {
  useWebSocket(); // Establish WebSocket connection
  const data = useTelemetryStore(state => state.data);
  const [selectedMission, setSelectedMission] = useState('isr_patrol');
  const [isRunning, setIsRunning] = useState(false);
  const [simSpeed, setSimSpeed] = useState(1);

  const apiCall = async (path: string, body?: object) => {
    try {
      const opts: RequestInit = body 
        ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
        : { method: 'POST' };
      const res = await fetch(`${API_BASE}${path}`, opts);
      return await res.json();
    } catch (e) {
      console.error('API call failed:', e);
    }
  };

  const handleStart = async () => {
    await apiCall('/api/mission/start', { mission_id: selectedMission });
    setIsRunning(true);
  };

  const handleStop = async () => {
    await apiCall('/api/mission/stop');
    setIsRunning(false);
  };

  const handleSpeedChange = async (speed: number) => {
    await apiCall('/api/simulation/speed', { speed });
    setSimSpeed(speed);
  };

  const handleInjectFault = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const faultId = e.target.value;
    if (!faultId) return;
    const fault = FAULT_TYPES.find(f => f.id === faultId);
    if (fault) {
      await apiCall('/api/fault/inject', {
        fault_type: fault.id,
        cylinder: fault.cyl,
        severity: 0.85,
        ramp_seconds: 45.0,
      });
    }
    e.target.value = '';
  };

  const handleClearFaults = async () => {
    await apiCall('/api/fault/clear');
  };

  const missionPhase = data?.mission_phase || '—';
  const missionTime = data?.mission_time 
    ? `${Math.floor(data.mission_time / 60)}:${String(Math.floor(data.mission_time % 60)).padStart(2, '0')}`
    : '0:00';

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '20px', overflow: 'auto' }}>
      {/* Mission Control */}
      <div>
        <div className="panel-header">
          <span style={{ fontSize: '14px' }}>⚙</span> Mission Control
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <select 
            value={selectedMission} 
            onChange={e => setSelectedMission(e.target.value)} 
            style={{ width: '100%' }}
            disabled={isRunning}
          >
            {MISSIONS.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button className={`button ${isRunning ? '' : 'active'}`} onClick={handleStart} disabled={isRunning}>
              ▶ Start
            </button>
            <button className="button" onClick={handleStop} disabled={!isRunning}>
              ■ Stop
            </button>
          </div>

          {isRunning && (
            <div style={{ fontSize: '11px', color: colors.accent, textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
              {missionPhase} • T+{missionTime}
            </div>
          )}
        </div>
      </div>

      {/* Simulation Speed */}
      <div>
        <div className="panel-header">
          <span style={{ fontSize: '14px' }}>⏱</span> Sim Speed
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          {[1, 2, 4, 8].map(speed => (
            <button
              key={speed}
              className={`button ${simSpeed === speed ? 'active' : ''}`}
              style={{ flex: 1, padding: '6px 4px', fontSize: '12px' }}
              onClick={() => handleSpeedChange(speed)}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Fault Injection */}
      <div>
        <div className="panel-header" style={{ color: colors.warning }}>
          <span style={{ fontSize: '14px' }}>⚡</span> Fault Injection
        </div>
        <select 
          onChange={handleInjectFault} 
          style={{ width: '100%', borderColor: colors.warning }} 
          defaultValue=""
        >
          <option value="" disabled>Inject Fault...</option>
          {FAULT_TYPES.map(f => (
            <option key={f.id} value={f.id}>{f.name}</option>
          ))}
        </select>
        <button 
          className="button" 
          style={{ width: '100%', marginTop: '8px', fontSize: '11px', borderColor: 'rgba(239,68,68,0.4)' }}
          onClick={handleClearFaults}
        >
          Clear All Faults
        </button>
        <div style={{ fontSize: '10px', color: colors.textMuted, marginTop: '8px', lineHeight: 1.5 }}>
          Inject faults to observe real-time divergence between physics model predictions (dashed) and actual sensor telemetry (solid).
        </div>
      </div>

      {/* Engine Specs */}
      <div style={{ marginTop: 'auto' }}>
        <div className="panel-header">
          <span style={{ fontSize: '14px' }}>🔧</span> Engine Specs
        </div>
        <div style={{ fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '6px', color: colors.textSecondary }}>
          {[
            ['Model', 'IO-360 (Simulated)'],
            ['Type', 'Horiz-Opposed 4-Cyl'],
            ['Displacement', '361 cu in'],
            ['Compression', '8.7:1'],
            ['Max RPM', '2,700'],
            ['Fuel', '100LL Avgas'],
          ].map(([label, value]) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>{label}</span>
              <span style={{ color: '#fff', fontFamily: 'var(--font-mono)', fontSize: '10px' }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
