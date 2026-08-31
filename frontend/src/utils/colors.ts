export const colors = {
  bgBase: '#05080f',
  bgPanel: 'rgba(10, 14, 23, 0.7)',
  accent: '#06b6d4',
  nominal: '#10b981',
  caution: '#f59e0b',
  warning: '#f97316',
  critical: '#ef4444',
  textPrimary: '#e2e8f0',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
  border: 'rgba(6, 182, 212, 0.15)',
  cylinderCold: '#3b82f6', // blue
  cylinderNormal: '#10b981', // green
  cylinderWarm: '#f59e0b', // amber
  cylinderHot: '#ef4444', // red
  chart: [
    '#38bdf8', // cyl 1
    '#a78bfa', // cyl 2
    '#f472b6', // cyl 3
    '#fbbf24', // cyl 4
  ]
};

export const getStatusColor = (val: number, cautionLow: number, nominalLow: number, nominalHigh: number, cautionHigh: number) => {
  if (val < cautionLow || val > cautionHigh) return colors.critical;
  if (val < nominalLow || val > nominalHigh) return colors.warning;
  return colors.nominal;
};

export const getCylinderColor = (cht: number) => {
  if (cht < 250) return colors.cylinderCold;
  if (cht < 400) return colors.cylinderNormal;
  if (cht < 460) return colors.cylinderWarm;
  return colors.cylinderHot;
};
