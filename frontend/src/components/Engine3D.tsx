import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { useTelemetryStore } from '../stores/telemetryStore';
import { getCylinderColor } from '../utils/colors';

const Cylinder = ({ position, rotation, index }: { position: [number, number, number], rotation: [number, number, number], index: number }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const data = useTelemetryStore(state => state.data);
  const materialRef = useRef<THREE.MeshStandardMaterial>(null);

  useFrame(() => {
    if (!data || !materialRef.current) return;
    
    // Update color based on CHT
    const cht = data.engine.cht[index];
    const targetColor = new THREE.Color(getCylinderColor(cht));
    materialRef.current.color.lerp(targetColor, 0.1);
    
    // Pulsing effect if there's a fault associated with this cylinder
    const fault = data.fault_diagnosis.predicted_fault;
    const isFaulty = fault !== 'normal' && data.fault_diagnosis.confidence > 0.6;
    
    // Simplified fault mapping - normally you'd map specific faults to cylinders based on SHAP
    if (isFaulty) {
      const time = Date.now() / 1000;
      materialRef.current.emissive = new THREE.Color(0xff0000);
      materialRef.current.emissiveIntensity = (Math.sin(time * 10) * 0.5 + 0.5) * 0.8;
    } else {
      materialRef.current.emissiveIntensity = 0;
    }
  });

  return (
    <mesh ref={meshRef} position={position} rotation={rotation} castShadow receiveShadow>
      <cylinderGeometry args={[0.5, 0.5, 1.2, 32]} />
      <meshStandardMaterial ref={materialRef} color="#3b82f6" metalness={0.6} roughness={0.4} />
      {/* Cooling fins */}
      {[...Array(6)].map((_, i) => (
        <mesh key={i} position={[0, -0.4 + i * 0.16, 0]}>
          <cylinderGeometry args={[0.55, 0.55, 0.05, 32]} />
          <meshStandardMaterial color="#222" metalness={0.8} roughness={0.2} />
        </mesh>
      ))}
    </mesh>
  );
};

const Crankshaft = () => {
  const groupRef = useRef<THREE.Group>(null);
  const data = useTelemetryStore(state => state.data);

  useFrame(() => {
    if (!groupRef.current || !data) return;
    // RPM to radians per frame (approximate visual speed)
    const speed = (data.engine.rpm / 60) * Math.PI * 2 * (1/60); 
    groupRef.current.rotation.x += speed;
  });

  return (
    <group ref={groupRef}>
      {/* Main shaft */}
      <mesh rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.2, 0.2, 4.5, 16]} />
        <meshStandardMaterial color="#888" metalness={0.9} roughness={0.1} />
      </mesh>
    </group>
  );
};

export const Engine3D: React.FC = () => {
  return (
    <div className="panel" style={{ height: '100%', padding: '0', overflow: 'hidden', position: 'relative' }}>
      <div className="panel-header" style={{ position: 'absolute', top: '16px', left: '16px', zIndex: 10, border: 'none' }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
        Engine Digital Twin
      </div>
      
      <div style={{ position: 'absolute', bottom: '16px', left: '16px', zIndex: 10, fontSize: '10px', color: 'rgba(255,255,255,0.5)' }}>
        Left Drag: Rotate | Scroll: Zoom
      </div>
      
      <div style={{ position: 'absolute', top: '16px', right: '16px', zIndex: 10, display: 'flex', flexDirection: 'column', gap: '4px', background: 'rgba(0,0,0,0.6)', padding: '8px', borderRadius: '4px' }}>
        <div style={{ fontSize: '10px', color: '#fff', marginBottom: '4px' }}>CHT Heatmap</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px' }}>
          <div style={{ width: '12px', height: '12px', background: '#3b82f6', borderRadius: '2px' }}></div> &lt;250°F (Cold)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px' }}>
          <div style={{ width: '12px', height: '12px', background: '#10b981', borderRadius: '2px' }}></div> 250-400°F (Nominal)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px' }}>
          <div style={{ width: '12px', height: '12px', background: '#f59e0b', borderRadius: '2px' }}></div> 400-460°F (Warm)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '10px' }}>
          <div style={{ width: '12px', height: '12px', background: '#ef4444', borderRadius: '2px' }}></div> &gt;460°F (Hot)
        </div>
      </div>

      <Canvas camera={{ position: [4, 3, 5], fov: 45 }}>
        <color attach="background" args={['#05080f']} />
        <ambientLight intensity={0.4} />
        <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
        <pointLight position={[-10, -10, -5]} intensity={0.5} />
        
        <group position={[0, -0.5, 0]}>
          <Crankshaft />
          {/* Flat-4 layout: Cylinders 1,3 on one side, 2,4 on the other */}
          <Cylinder index={0} position={[-1, 0, 1.2]} rotation={[Math.PI / 2, 0, 0]} />
          <Cylinder index={1} position={[1, 0, 1.2]} rotation={[-Math.PI / 2, 0, 0]} />
          <Cylinder index={2} position={[-1, 0, -1.2]} rotation={[Math.PI / 2, 0, 0]} />
          <Cylinder index={3} position={[1, 0, -1.2]} rotation={[-Math.PI / 2, 0, 0]} />
          
          {/* Central block */}
          <mesh>
            <boxGeometry args={[1.2, 1, 4]} />
            <meshStandardMaterial color="#333" metalness={0.7} roughness={0.3} />
          </mesh>
        </group>
        
        <OrbitControls enablePan={false} maxPolarAngle={Math.PI / 2 + 0.2} minDistance={3} maxDistance={10} />
        <gridHelper args={[10, 20, '#06b6d4', '#111']} position={[0, -2, 0]} />
      </Canvas>
    </div>
  );
};
