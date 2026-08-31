import React from 'react';
import { TelemetryGauges } from './TelemetryGauges';
import { TelemetryCharts } from './TelemetryCharts';
import { Engine3D } from './Engine3D';
import { HealthStatus } from './HealthStatus';
import { FaultAlerts } from './FaultAlerts';
import { ShapWaterfall } from './ShapWaterfall';
import { RulCurve } from './RulCurve';

export const Dashboard: React.FC = () => {
  return (
    <div className="dashboard-grid">
      <div className="top-row">
        <TelemetryGauges />
        <TelemetryCharts />
        <Engine3D />
        <HealthStatus />
      </div>
      <div className="bottom-row">
        <FaultAlerts />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', minHeight: 0 }}>
          <ShapWaterfall />
          <RulCurve />
        </div>
      </div>
    </div>
  );
};
