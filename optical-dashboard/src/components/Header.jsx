import React from 'react';
import { Activity } from 'lucide-react';

export default function Header() {
  return (
    <header className="glass-panel" style={{
      padding: '1.2rem 2rem',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderTop: 'none',
      borderLeft: 'none',
      borderRight: 'none',
      zIndex: 10
    }}>
      <div>
        <h1 className="text-gradient" style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.5px' }}>
          ONOS-WDM Topology Explorer
        </h1>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
          Laboratorio de Comunicaciones Ópticas Virtualizado
        </div>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{ 
          background: 'rgba(56, 189, 248, 0.1)', 
          color: 'var(--accent)',
          padding: '4px 12px',
          borderRadius: '20px',
          fontSize: '0.8rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <Activity size={14} />
          <span>Live View</span>
        </div>
      </div>
    </header>
  );
}
