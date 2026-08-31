import React from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';

export const FaultAlerts: React.FC = () => {
  const alerts = useTelemetryStore(state => state.alerts);
  const data = useTelemetryStore(state => state.data);

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          Fault Alerts & Diagnosis
        </div>
        {data && data.fault_diagnosis.predicted_fault !== 'normal' && (
          <div className="animate-pulse-glow" style={{ width: '8px', height: '8px', borderRadius: '50%', background: colors.critical }}></div>
        )}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '4px' }}>
        {alerts.length === 0 ? (
          <div style={{ color: colors.textMuted, fontSize: '12px', textAlign: 'center', marginTop: '20px' }}>No active alerts</div>
        ) : (
          alerts.map(alert => (
            <div key={alert.id} className="animate-slide-up" style={{
              background: 'rgba(0,0,0,0.4)',
              borderLeft: `3px solid ${alert.severity === 'critical' ? colors.critical : alert.severity === 'warning' ? colors.warning : colors.accent}`,
              padding: '8px 12px',
              borderRadius: '0 4px 4px 0',
              fontSize: '12px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontWeight: 'bold', textTransform: 'uppercase', color: alert.severity === 'critical' ? colors.critical : alert.severity === 'warning' ? colors.warning : colors.accent }}>{alert.type}</span>
                <span style={{ color: colors.textSecondary, fontFamily: 'var(--font-mono)' }}>T+{Math.floor(alert.time)}s</span>
              </div>
              <div style={{ color: colors.textPrimary }}>{alert.message}</div>
            </div>
          ))
        )}
      </div>
      
      {/* Current Diagnosis Summary */}
      {data && (
        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ fontSize: '10px', color: colors.textSecondary, marginBottom: '8px' }}>CURRENT AI DIAGNOSIS</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 'bold', color: data.fault_diagnosis.predicted_fault === 'normal' ? colors.nominal : colors.warning, textTransform: 'uppercase' }}>
              {data.fault_diagnosis.predicted_fault.replace('_', ' ')}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: colors.accent }}>
              {(data.fault_diagnosis.confidence * 100).toFixed(1)}% CONF
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
