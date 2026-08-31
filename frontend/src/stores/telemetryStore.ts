import { create } from 'zustand';

export interface TelemetryData {
  timestamp: number;
  mission_time: number;
  mission_phase: string;
  engine: {
    rpm: number;
    map_inHg: number;
    fuel_flow_gph: number;
    cht: number[];
    egt: number[];
    oil_temp_f: number;
    oil_press_psi: number;
    vib_g_rms: number;
    crankcase_press: number;
    battery_v: number;
    alternator_a: number;
  };
  physics_prediction: {
    cht: number[];
    egt: number[];
    oil_temp_f: number;
    oil_press_psi: number;
  };
  anomaly: {
    score: number;
    mahalanobis_distance: number;
    threshold: number;
    is_anomaly: boolean;
    residuals: Record<string, number>;
  };
  health: {
    health_index: number;
    rul_hours: number;
    rul_lower: number;
    rul_upper: number;
    trend: 'stable' | 'degrading' | 'improving' | string;
  };
  fault_diagnosis: {
    predicted_fault: string;
    confidence: number;
    fault_probabilities: Record<string, number>;
    shap_contributions: Array<{feature: string; value: number; impact: number}>;
  };
  active_faults: string[];
  simulation_speed: number;
}

interface TelemetryStore {
  data: TelemetryData | null;
  history: TelemetryData[];
  isConnected: boolean;
  selectedMission: string;
  alerts: Array<{ id: string; time: number; type: string; message: string; severity: 'info' | 'warning' | 'critical' }>;
  
  setData: (data: TelemetryData) => void;
  setConnectionStatus: (status: boolean) => void;
  setMission: (mission: string) => void;
  addAlert: (alert: { type: string; message: string; severity: 'info' | 'warning' | 'critical' }) => void;
}

export const useTelemetryStore = create<TelemetryStore>((set) => ({
  data: null,
  history: [],
  isConnected: false,
  selectedMission: 'default',
  alerts: [],
  
  setData: (newData) => set((state) => {
    const newHistory = [...state.history, newData].slice(-300); // keep last 300
    
    // Check for new faults to generate alerts automatically
    const newAlerts = [...state.alerts];
    if (newData.fault_diagnosis.predicted_fault !== 'normal') {
      const isExisting = newAlerts.some(a => a.type === newData.fault_diagnosis.predicted_fault && (newData.timestamp - a.time) < 10);
      if (!isExisting && newData.fault_diagnosis.confidence > 0.8) {
        newAlerts.unshift({
          id: Date.now().toString(),
          time: newData.timestamp,
          type: newData.fault_diagnosis.predicted_fault,
          message: `Detected ${newData.fault_diagnosis.predicted_fault} with ${(newData.fault_diagnosis.confidence * 100).toFixed(1)}% confidence`,
          severity: newData.fault_diagnosis.confidence > 0.95 ? 'critical' : 'warning'
        });
      }
    }
    
    // Keep alerts bounded
    const boundedAlerts = newAlerts.slice(0, 50);

    return { data: newData, history: newHistory, alerts: boundedAlerts };
  }),
  
  setConnectionStatus: (status) => set({ isConnected: status }),
  setMission: (mission) => set({ selectedMission: mission }),
  
  addAlert: (alert) => set((state) => ({
    alerts: [{ id: Date.now().toString(), time: state.data?.timestamp || Date.now()/1000, ...alert }, ...state.alerts].slice(0, 50)
  })),
}));
