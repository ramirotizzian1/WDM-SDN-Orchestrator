import React, { useState } from 'react';
import { Activity, Play } from 'lucide-react';

export default function Header() {
  const [lambda, setLambda] = useState('');
  const [source, setSource] = useState('ROADM-1');
  const [target, setTarget] = useState('ROADM-2');
  const [modulation, setModulation] = useState('QPSK');
  const [loading, setLoading] = useState(false);

  const handleProvision = async () => {
    setLoading(true);
    try {
      const payload = { source, target, modulation };
      if (lambda) {
        payload.force_lambda = parseInt(lambda, 10);
      }
      
      const res = await fetch('http://localhost:5000/api/provision', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if(data.status === 'success') {
        alert(`Ruta establecida con éxito. Lambda usada: ${data.lambda}\nRuta: ${data.path.join(' ➔ ')}`);
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (e) {
      alert('Error de conexión con el Agente SDN en el puerto 5000');
    } finally {
      setLoading(false);
    }
  };

  const handleFree = async () => {
    if (!lambda) {
      alert("Para liberar espectro, debes ingresar el número de Lambda exacto en el cuadro de texto.");
      return;
    }
    setLoading(true);
    try {
      const payload = { source, target, force_lambda: parseInt(lambda, 10) };
      const res = await fetch('http://localhost:5000/api/free', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if(data.status === 'success') {
        alert(data.message);
      } else {
        alert(`Error: ${data.message}`);
      }
    } catch (e) {
      alert('Error de conexión con el Agente SDN en el puerto 5000');
    } finally {
      setLoading(false);
    }
  };

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
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        
        {/* Controles RWA y Ruteo Dinámico */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', background: 'rgba(0,0,0,0.3)', padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>De:</span>
            <select 
              value={source} 
              onChange={e => setSource(e.target.value)}
              style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid var(--panel-border)', borderRadius: '4px', padding: '2px 4px', fontSize: '0.85rem', outline: 'none' }}
            >
              <option value="ROADM-1">ROADM-1</option>
              <option value="ROADM-2">ROADM-2</option>
              <option value="ROADM-3">ROADM-3</option>
              <option value="ROADM-4">ROADM-4</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>A:</span>
            <select 
              value={target} 
              onChange={e => setTarget(e.target.value)}
              style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid var(--panel-border)', borderRadius: '4px', padding: '2px 4px', fontSize: '0.85rem', outline: 'none' }}
            >
              <option value="ROADM-1">ROADM-1</option>
              <option value="ROADM-2">ROADM-2</option>
              <option value="ROADM-3">ROADM-3</option>
              <option value="ROADM-4">ROADM-4</option>
            </select>
          </div>

          <div style={{ width: '1px', height: '20px', background: 'var(--panel-border)' }}></div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Modulación:</span>
            <select 
              value={modulation} 
              onChange={e => setModulation(e.target.value)}
              style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid var(--panel-border)', borderRadius: '4px', padding: '2px 4px', fontSize: '0.85rem', outline: 'none' }}
            >
              <option value="QPSK">QPSK (Máx alcance)</option>
              <option value="16-QAM">16-QAM</option>
              <option value="64-QAM">64-QAM (Alta capacidad)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Lambda:</span>
            <input 
              type="number" 
              placeholder="Auto" 
              value={lambda}
              onChange={(e) => setLambda(e.target.value)}
              style={{ 
                width: '50px', 
                background: 'rgba(255,255,255,0.1)', 
                border: '1px solid var(--panel-border)', 
                color: 'white', 
                borderRadius: '4px', 
                padding: '4px 6px',
                fontSize: '0.85rem'
              }} 
              min="1" max="96"
            />
          </div>

          <button 
            onClick={handleProvision}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'var(--accent)', color: 'white', border: 'none',
              padding: '6px 12px', borderRadius: '4px', fontSize: '0.85rem',
              fontWeight: 'bold', cursor: loading ? 'wait' : 'pointer',
              opacity: loading ? 0.7 : 1, marginLeft: '4px'
            }}
          >
            <Play size={14} />
            {loading ? '...' : 'Aprovisionar'}
          </button>

          <button 
            onClick={handleFree}
            disabled={loading}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'rgba(239, 68, 68, 0.8)', color: 'white', border: 'none',
              padding: '6px 12px', borderRadius: '4px', fontSize: '0.85rem',
              fontWeight: 'bold', cursor: loading ? 'wait' : 'pointer',
              opacity: loading ? 0.7 : 1, marginLeft: '4px'
            }}
            title="Ingresa la Lambda a liberar"
          >
            {loading ? '...' : 'Liberar'}
          </button>
        </div>

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
