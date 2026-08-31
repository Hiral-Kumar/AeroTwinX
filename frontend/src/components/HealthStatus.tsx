import React from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';

export const HealthStatus: React.FC = () => {
  const data = useTelemetryStore(state => state.data);

  if (!data) return <div className="panel">Waiting...</div>;

  const { health } = data;
  const hi = health.health_index;
  
  let statusColor = colors.nominal;
  let statusText = 'NOMINAL';
  
  if (hi < 40) {
    statusColor = colors.critical;
    statusText = 'CRITICAL';
  } else if (hi < 70) {
    statusColor = colors.warning;
    statusText = 'WARNING';
  } else if (hi < 90) {
    statusColor = colors.caution;
    statusText = 'CAUTION';
  }

  // Circular progress for HI
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (hi / 100) * circumference;

  return (
    <div className="panel" style={{ height: '100%', position: 'relative' }}>
      <div className="panel-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        Health Status
      </div>
      
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'space-around' }}>
        
        {/* HI Gauge */}
        <div style={{ position: 'relative', width: '140px', height: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="140" height="140" style={{ transform: 'rotate(-90deg)', position: 'absolute' }}>
            <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="12" />
            <circle cx="70" cy="70" r={radius} fill="none" stroke={statusColor} strokeWidth="12" strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
          </svg>
          <div style={{ textAlign: 'center', zIndex: 1 }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold', fontFamily: 'var(--font-mono)', color: statusColor, textShadow: `0 0 10px ${statusColor}40` }}>
              {hi.toFixed(1)}<span style={{ fontSize: '16px' }}>%</span>
            </div>
            <div style={{ fontSize: '10px', color: colors.textSecondary, letterSpacing: '1px' }}>HEALTH INDEX</div>
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '10px', color: colors.textSecondary, marginBottom: '4px', letterSpacing: '1px' }}>SYSTEM STATUS</div>
            <div style={{ color: statusColor, fontWeight: 'bold', fontSize: '18px', letterSpacing: '2px', textShadow: `0 0 10px ${statusColor}60` }}>
              {statusText}
            </div>
          </div>
          
          <div>
            <div style={{ fontSize: '10px', color: colors.textSecondary, marginBottom: '4px', letterSpacing: '1px' }}>REMAINING USEFUL LIFE</div>
            <div style={{ fontSize: '24px', fontFamily: 'var(--font-mono)', fontWeight: 'bold' }}>
              {health.rul_hours} <span style={{ fontSize: '12px', color: colors.textSecondary }}>HRS</span>
            </div>
            <div style={{ fontSize: '10px', color: colors.textSecondary }}>
              90% CI: [{health.rul_lower} - {health.rul_upper}]
            </div>
          </div>

          <div>
            <div style={{ fontSize: '10px', color: colors.textSecondary, marginBottom: '4px', letterSpacing: '1px' }}>TREND</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {health.trend === 'stable' && <span style={{ color: colors.nominal }}>→ STABLE</span>}
              {health.trend === 'degrading' && <span style={{ color: colors.warning }}>↘ DEGRADING</span>}
              {health.trend === 'improving' && <span style={{ color: colors.nominal }}>↗ IMPROVING</span>}
              {health.trend !== 'stable' && health.trend !== 'degrading' && health.trend !== 'improving' && <span>{health.trend}</span>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
