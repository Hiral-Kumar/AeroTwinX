import React, { useEffect, useRef } from 'react';
import { useTelemetryStore, type TelemetryData } from '../stores/telemetryStore';
import { colors } from '../utils/colors';

const StripChart = ({ title, dataKey, history, unit, min, max, isArray = true, showPrediction = true }: { title: string, dataKey: 'cht' | 'egt', history: TelemetryData[], unit: string, min: number, max: number, isArray?: boolean, showPrediction?: boolean }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      // Draw grid
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();

      if (history.length === 0) return;

      const xStep = width / 300; // 300 points max

      const plotLine = (getValue: (d: TelemetryData) => number, color: string, isDashed: boolean = false) => {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        if (isDashed) {
          ctx.setLineDash([4, 4]);
          ctx.lineWidth = 1.5;
        } else {
          ctx.setLineDash([]);
        }

        for (let i = 0; i < history.length; i++) {
          const val = getValue(history[i]);
          const x = width - (history.length - 1 - i) * xStep;
          const y = height - ((Math.max(min, Math.min(max, val)) - min) / (max - min)) * height;
          
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      };

      if (isArray) {
        for (let cyl = 0; cyl < 4; cyl++) {
          // Plot actual
          plotLine(d => (d.engine[dataKey] as number[])[cyl], colors.chart[cyl]);
          // Plot prediction
          if (showPrediction) {
            plotLine(d => (d.physics_prediction[dataKey] as number[])[cyl], colors.chart[cyl], true);
          }
        }
      }
    };

    let animationId: number;
    const loop = () => {
      render();
      animationId = requestAnimationFrame(loop);
    };
    loop();

    return () => cancelAnimationFrame(animationId);
  }, [history, min, max, dataKey, isArray, showPrediction]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '120px', position: 'relative' }}>
      <div style={{ fontSize: '10px', color: colors.textSecondary, marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
        <span>{title} ({unit})</span>
        <span>{max}</span>
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <canvas ref={canvasRef} width={800} height={200} style={{ width: '100%', height: '100%', display: 'block' }} />
      </div>
      <div style={{ fontSize: '10px', color: colors.textSecondary, marginTop: '2px', textAlign: 'right' }}>{min}</div>
      <div style={{ position: 'absolute', top: '15px', right: '10px', display: 'flex', gap: '8px', fontSize: '9px', background: 'rgba(0,0,0,0.5)', padding: '2px 6px', borderRadius: '4px' }}>
        {colors.chart.map((c, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '2px', background: c }}></span> Cyl {i+1}
          </div>
        ))}
      </div>
    </div>
  );
};

export const TelemetryCharts: React.FC = () => {
  const history = useTelemetryStore(state => state.history);

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/></svg>
        Telemetry Charts
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, overflowY: 'auto' }}>
        <StripChart title="Cylinder Head Temp" dataKey="cht" history={history} unit="°F" min={200} max={500} />
        <StripChart title="Exhaust Gas Temp" dataKey="egt" history={history} unit="°F" min={1100} max={1600} />
      </div>
    </div>
  );
};
