import React from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';

export const ShapWaterfall: React.FC = () => {
  const data = useTelemetryStore(state => state.data);

  if (!data) return <div className="panel">Waiting...</div>;

  const shap = data.fault_diagnosis.shap_contributions;
  if (!shap || shap.length === 0) return <div className="panel">No SHAP data</div>;

  const maxImpact = Math.max(...shap.map(s => Math.abs(s.impact)));

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        Root Cause Analysis (SHAP)
      </div>
      
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', paddingRight: '8px' }}>
        {shap.map((s, i) => {
          const width = (Math.abs(s.impact) / maxImpact) * 100;
          const isPositive = s.impact > 0;
          return (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 40px', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
              <div style={{ color: colors.textSecondary, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{s.feature}</div>
              
              <div style={{ position: 'relative', height: '16px', display: 'flex', alignItems: 'center' }}>
                <div style={{ position: 'absolute', left: '50%', width: '1px', height: '100%', background: 'rgba(255,255,255,0.2)' }}></div>
                
                {isPositive ? (
                  <div style={{ marginLeft: '50%', width: `${width / 2}%`, height: '12px', background: colors.critical, borderRadius: '0 2px 2px 0', transition: 'width 0.3s ease' }}></div>
                ) : (
                  <div style={{ width: `${width / 2}%`, height: '12px', background: colors.cylinderCold, marginLeft: `calc(50% - ${width / 2}%)`, borderRadius: '2px 0 0 2px', transition: 'width 0.3s ease' }}></div>
                )}
              </div>
              
              <div style={{ fontFamily: 'var(--font-mono)', textAlign: 'right', color: isPositive ? colors.critical : colors.cylinderCold }}>
                {s.impact > 0 ? '+' : ''}{s.impact.toFixed(3)}
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', fontSize: '10px', marginTop: '12px', color: colors.textSecondary }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '8px', height: '8px', background: colors.cylinderCold }}></div> Drives to Normal
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '8px', height: '8px', background: colors.critical }}></div> Drives to Fault
        </div>
      </div>
    </div>
  );
};
