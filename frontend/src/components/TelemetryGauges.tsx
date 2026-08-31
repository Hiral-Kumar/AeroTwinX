import React from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';
import { formatNumber } from '../utils/formatters';

interface GaugeProps {
  label: string;
  value: number;
  unit: string;
  min: number;
  max: number;
  arcs: Array<{ min: number; max: number; color: string }>;
}

const CircularGauge: React.FC<GaugeProps> = ({ label, value, unit, min, max, arcs }) => {
  const radius = 40;
  const cx = 50;
  const cy = 50;
  const startAngle = 135;
  const endAngle = 405;
  const angleRange = endAngle - startAngle;

  const valueToAngle = (val: number) => {
    const clamped = Math.max(min, Math.min(max, val));
    const ratio = (clamped - min) / (max - min);
    return startAngle + ratio * angleRange;
  };

  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
      x: centerX + radius * Math.cos(angleInRadians),
      y: centerY + radius * Math.sin(angleInRadians)
    };
  };

  const describeArc = (x: number, y: number, r: number, start: number, end: number) => {
    const startPt = polarToCartesian(x, y, r, start);
    const endPt = polarToCartesian(x, y, r, end);
    const largeArcFlag = end - start <= 180 ? '0' : '1';
    return ['M', startPt.x, startPt.y, 'A', r, r, 0, largeArcFlag, 1, endPt.x, endPt.y].join(' ');
  };

  const needleAngle = valueToAngle(value);
  const needleLen = 30;
  const needlePt = polarToCartesian(cx, cy, needleLen, needleAngle);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '10px 0' }}>
      <svg width="100%" viewBox="0 0 100 90" style={{ overflow: 'visible' }}>
        {/* Background track */}
        <path d={describeArc(cx, cy, radius, startAngle, endAngle)} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="6" strokeLinecap="round" />
        
        {/* Arcs */}
        {arcs.map((arc, i) => (
          <path key={i}
            d={describeArc(cx, cy, radius, valueToAngle(arc.min), valueToAngle(arc.max))}
            fill="none" stroke={arc.color} strokeWidth="6" strokeLinecap="round"
          />
        ))}
        
        {/* Needle */}
        <line x1={cx} y1={cy} x2={needlePt.x} y2={needlePt.y} stroke={colors.textPrimary} strokeWidth="2" strokeLinecap="round" style={{ transition: 'all 0.2s ease-out' }} />
        <circle cx={cx} cy={cy} r="4" fill={colors.accent} />
        
        {/* Value text */}
        <text x="50" y="80" textAnchor="middle" fill={colors.textPrimary} fontSize="14" className="gauge-value" fontWeight="bold">
          {formatNumber(value, value < 10 ? 1 : 0)}
        </text>
        <text x="50" y="92" textAnchor="middle" fill={colors.textSecondary} fontSize="8">
          {unit}
        </text>
      </svg>
      <div style={{ fontSize: '10px', color: colors.textSecondary, marginTop: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}>{label}</div>
    </div>
  );
};

export const TelemetryGauges: React.FC = () => {
  const data = useTelemetryStore(state => state.data);

  if (!data) return <div className="panel"><div className="panel-header">Engine Gauges</div><div>Waiting for telemetry...</div></div>;

  const { engine } = data;

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: colors.accent, boxShadow: `0 0 8px ${colors.accent}` }}></span>
        Engine Gauges
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', flex: 1, overflowY: 'auto' }}>
        <CircularGauge 
          label="RPM" value={engine.rpm} unit="RPM" min={0} max={3000}
          arcs={[
            { min: 0, max: 2000, color: 'rgba(255,255,255,0.2)' },
            { min: 2000, max: 2500, color: colors.nominal },
            { min: 2500, max: 2700, color: colors.warning },
            { min: 2700, max: 3000, color: colors.critical }
          ]}
        />
        <CircularGauge 
          label="MAP" value={engine.map_inHg} unit="inHg" min={0} max={35}
          arcs={[{ min: 15, max: 30, color: colors.nominal }, { min: 30, max: 35, color: colors.critical }]}
        />
        <CircularGauge 
          label="Oil Press" value={engine.oil_press_psi} unit="PSI" min={0} max={100}
          arcs={[
            { min: 0, max: 25, color: colors.critical },
            { min: 25, max: 55, color: colors.warning },
            { min: 55, max: 85, color: colors.nominal },
            { min: 85, max: 100, color: colors.critical }
          ]}
        />
        <CircularGauge 
          label="Oil Temp" value={engine.oil_temp_f} unit="°F" min={100} max={250}
          arcs={[
            { min: 100, max: 165, color: colors.warning },
            { min: 165, max: 200, color: colors.nominal },
            { min: 200, max: 230, color: colors.warning },
            { min: 230, max: 250, color: colors.critical }
          ]}
        />
        <CircularGauge 
          label="Fuel Flow" value={engine.fuel_flow_gph} unit="GPH" min={0} max={25}
          arcs={[{ min: 8, max: 18, color: colors.nominal }]}
        />
        <CircularGauge 
          label="Vibration" value={engine.vib_g_rms} unit="G" min={0} max={3}
          arcs={[
            { min: 0, max: 0.8, color: colors.nominal },
            { min: 0.8, max: 1.2, color: colors.warning },
            { min: 1.2, max: 3.0, color: colors.critical }
          ]}
        />
      </div>
    </div>
  );
};
