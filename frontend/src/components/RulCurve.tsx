import React, { useEffect, useRef } from 'react';
import { useTelemetryStore } from '../stores/telemetryStore';
import { colors } from '../utils/colors';

export const RulCurve: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const data = useTelemetryStore(state => state.data);
  const history = useTelemetryStore(state => state.history);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      // Grid
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();

      // Failure threshold line
      const thresholdY = height - (30 / 100) * height; // 30% HI threshold
      ctx.strokeStyle = colors.critical;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(0, thresholdY);
      ctx.lineTo(width, thresholdY);
      ctx.stroke();
      ctx.setLineDash([]);
      
      ctx.fillStyle = colors.critical;
      ctx.font = '10px sans-serif';
      ctx.fillText('FAILURE THRESHOLD (30%)', 5, thresholdY - 5);

      if (history.length < 2) return;

      const currentX = width * 0.3; // Current time is at 30% of chart width
      
      // Plot Historical HI
      ctx.beginPath();
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 2;
      
      const histStep = currentX / history.length;
      for(let i=0; i<history.length; i++) {
        const x = i * histStep;
        const y = height - (history[i].health.health_index / 100) * height;
        if (i===0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Plot Future Projection
      const { health_index, rul_hours, rul_lower, rul_upper } = data.health;
      
      const futureWidth = width - currentX;
      // Map max RUL (e.g. 1000) to remaining width
      const maxPlotRul = 1000;
      
      const projX = currentX + (rul_hours / maxPlotRul) * futureWidth;
      const projLowerX = currentX + (rul_lower / maxPlotRul) * futureWidth;
      const projUpperX = currentX + (rul_upper / maxPlotRul) * futureWidth;

      // Draw projection line (mean)
      ctx.beginPath();
      ctx.strokeStyle = colors.warning;
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.moveTo(currentX, height - (health_index / 100) * height);
      // Curve to threshold
      ctx.quadraticCurveTo(currentX + (projX - currentX) * 0.5, height - (health_index / 100) * height, projX, thresholdY);
      ctx.stroke();
      ctx.setLineDash([]);

      // Fill confidence interval
      ctx.beginPath();
      ctx.moveTo(currentX, height - (health_index / 100) * height);
      ctx.quadraticCurveTo(currentX + (projUpperX - currentX) * 0.5, height - (health_index / 100) * height, projUpperX, thresholdY);
      ctx.lineTo(projLowerX, thresholdY);
      ctx.quadraticCurveTo(currentX + (projLowerX - currentX) * 0.5, height - (health_index / 100) * height, currentX, height - (health_index / 100) * height);
      ctx.fillStyle = 'rgba(245, 158, 11, 0.15)'; // warning color transparent
      ctx.fill();

      // Current point marker
      const currentY = height - (health_index / 100) * height;
      ctx.beginPath();
      ctx.arc(currentX, currentY, 4, 0, Math.PI * 2);
      ctx.fillStyle = colors.accent;
      ctx.fill();
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 1;
      ctx.stroke();

      // RUL marker
      ctx.beginPath();
      ctx.arc(projX, thresholdY, 4, 0, Math.PI * 2);
      ctx.fillStyle = colors.warning;
      ctx.fill();
    };

    render();
  }, [data, history]);

  return (
    <div className="panel" style={{ height: '100%' }}>
      <div className="panel-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        RUL Projection
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <canvas ref={canvasRef} width={600} height={150} style={{ width: '100%', height: '100%', display: 'block' }} />
      </div>
    </div>
  );
};
