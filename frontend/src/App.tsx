import React from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { MissionTimeline } from './components/MissionTimeline';
import { useTelemetryStore } from './stores/telemetryStore';
import { colors } from './utils/colors';

const App: React.FC = () => {
  const isConnected = useTelemetryStore(state => state.isConnected);

  return (
    <div className="layout-grid">
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={colors.accent} strokeWidth="2"><path d="M12 2L2 22h20L12 2z"/></svg>
            <h1 style={{ margin: 0, fontSize: '24px', letterSpacing: '2px', color: '#fff' }}>
              AEROTWIN<span style={{ color: colors.accent }}>X</span>
            </h1>
          </div>
          <div style={{ color: colors.textSecondary, fontSize: '12px', letterSpacing: '1px' }}>| AI DIGITAL TWIN</div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
            <div className={isConnected ? "animate-pulse-glow" : ""} style={{ width: '8px', height: '8px', borderRadius: '50%', background: isConnected ? colors.nominal : colors.critical }}></div>
            <span style={{ color: isConnected ? colors.nominal : colors.critical, fontWeight: 'bold' }}>
              {isConnected ? 'LIVE (10 Hz)' : 'DISCONNECTED'}
            </span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: colors.accent }}>
            {new Date().toISOString().split('T')[1].split('.')[0]} UTC
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="main-content">
        <Sidebar />
        <Dashboard />
      </div>

      {/* Footer */}
      <footer style={{ height: '60px' }}>
        <MissionTimeline />
      </footer>
    </div>
  );
};

export default App;
