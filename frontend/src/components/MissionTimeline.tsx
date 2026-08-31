import React from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';
import { formatTime } from '../utils/formatters';

export const MissionTimeline: React.FC = () => {
  const data = useTelemetryStore(state => state.data);
  const alerts = useTelemetryStore(state => state.alerts);

  if (!data) return <div className="panel" style={{ height: '100%', display: 'flex', alignItems: 'center' }}>Waiting...</div>;

  const totalMissionTime = 3600; // Assume 1 hour for display if not provided
  const progress = Math.min(100, (data.mission_time / totalMissionTime) * 100);

  // Define static mission phases for visualization
  const phases = [
    { name: 'TAKEOFF', start: 0, end: 5 },
    { name: 'CLIMB', start: 5, end: 15 },
    { name: 'CRUISE', start: 15, end: 75 },
    { name: 'DESCENT', start: 75, end: 95 },
    { name: 'LANDING', start: 95, end: 100 }
  ];

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{ fontSize: '18px', fontWeight: 'bold', fontFamily: 'var(--font-mono)' }}>
            T+ {formatTime(data.mission_time)}
          </div>
          <div style={{ background: 'rgba(6, 182, 212, 0.2)', color: colors.accent, padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', letterSpacing: '1px' }}>
            {data.mission_phase}
          </div>
        </div>
        <div style={{ fontSize: '12px', color: colors.textSecondary, fontFamily: 'var(--font-mono)' }}>
          SIM SPEED: {data.simulation_speed}x
        </div>
      </div>

      <div style={{ position: 'relative', height: '24px', background: 'rgba(0,0,0,0.5)', borderRadius: '4px', border: `1px solid ${colors.border}` }}>
        
        {/* Phase markers */}
        {phases.map((phase, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${phase.start}%`,
            width: `${phase.end - phase.start}%`,
            height: '100%',
            borderRight: i < phases.length - 1 ? '1px dashed rgba(255,255,255,0.1)' : 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '9px',
            color: 'rgba(255,255,255,0.3)',
            letterSpacing: '1px'
          }}>
            {phase.name}
          </div>
        ))}

        {/* Progress bar */}
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          height: '100%',
          width: `${progress}%`,
          background: `linear-gradient(90deg, rgba(6,182,212,0.1) 0%, rgba(6,182,212,0.4) 100%)`,
          borderRight: `2px solid ${colors.accent}`,
          transition: 'width 0.1s linear'
        }}></div>

        {/* Fault markers */}
        {alerts.map(alert => {
          // Approximate alert position
          const alertProgress = (alert.time / totalMissionTime) * 100;
          if (alertProgress > 100) return null;
          
          return (
            <div key={alert.id} title={alert.type} style={{
              position: 'absolute',
              left: `${alertProgress}%`,
              top: '50%',
              transform: 'translate(-50%, -50%)',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: alert.severity === 'critical' ? colors.critical : colors.warning,
              boxShadow: `0 0 5px ${alert.severity === 'critical' ? colors.critical : colors.warning}`
            }}></div>
          );
        })}
      </div>
    </div>
  );
};
