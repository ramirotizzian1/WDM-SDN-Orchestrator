import React from 'react';
import { Info, MapPin, Activity, Zap } from 'lucide-react';

export default function SidePanel({ element }) {
  if (!element) {
    return (
      <div className="glass-panel" style={{
        width: '340px',
        borderTop: 'none', borderRight: 'none', borderBottom: 'none',
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-muted)',
        textAlign: 'center'
      }}>
        <Info size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
        <p>Selecciona un ROADM o Enlace de fibra para ver sus propiedades.</p>
      </div>
    );
  }

  const isNode = element.type === 'node';
  const data = element.data;

  return (
    <div className="glass-panel" style={{
      width: '340px',
      borderTop: 'none', borderRight: 'none', borderBottom: 'none',
      padding: '2rem',
      overflowY: 'auto'
    }}>
      <h2 style={{ 
        fontSize: '1.2rem', 
        fontWeight: 600, 
        marginTop: 0, 
        marginBottom: '1.5rem', 
        color: 'var(--accent)',
        borderBottom: '1px solid var(--panel-border)',
        paddingBottom: '0.8rem',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        {isNode ? <Activity size={20} /> : <Zap size={20} />}
        {isNode ? 'Detalles del ROADM' : 'Detalles del Enlace WDM'}
      </h2>

      <div style={{
        background: 'rgba(0,0,0,0.3)',
        border: '1px solid var(--panel-border)',
        borderRadius: '12px',
        padding: '1.2rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.8rem',
        transition: 'all 0.3s ease',
        boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
      }}>
        
        {isNode ? (
          <>
            <InfoRow label="ID Nodo" value={data.id} highlight />
            <InfoRow label="Hardware" value={data.hardware || data.type.toUpperCase()} />
            <InfoRow label="Ubicación" value={data.location} icon={<MapPin size={14} />} />
            {data.degrees && <InfoRow label="Grados (WSS)" value={data.degrees} />}
            {data.mgmt_ip && <InfoRow label="IP Gestión" value={data.mgmt_ip} />}
            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed var(--panel-border)' }}>
              <InfoRow 
                label="Estado" 
                value={data.status ? data.status.toUpperCase() : "ONLINE"} 
                color={data.status === 'down' ? 'var(--accent-danger)' : (data.status === 'degraded' ? '#fbbf24' : 'var(--accent-success)')} 
              />
            </div>
            
            <OnosMetrics nodeId={data.id} />
          </>
        ) : (
          <>
            <InfoRow label="Origen" value={data.source} highlight />
            <InfoRow label="Destino" value={data.target} highlight />
            <InfoRow label="Tipo Fibra" value={data.type} />
            <InfoRow label="Distancia" value={`${data.length_km} km`} />
            {data.spans && <InfoRow label="Spans Amplificación" value={data.spans} />}
            {data.modulation && <InfoRow label="Modulación" value={data.modulation} />}
            {data.osnr_db && <InfoRow label="OSNR (QoT)" value={`${data.osnr_db} dB`} color="#38bdf8" />}
            
            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed var(--panel-border)' }}>
              <InfoRow label="Atenuación Fibra" value={`${data.loss_coef_db_km} dB/km`} />
              <InfoRow 
                label="Pérdida Distancia" 
                value={`${(data.length_km * data.loss_coef_db_km).toFixed(2)} dB`} 
                color="var(--text-muted)" 
              />
              {data.status && (
                <div style={{ marginTop: '0.5rem' }}>
                  <InfoRow 
                    label="Estado WDM" 
                    value={data.status.toUpperCase()} 
                    color={data.status === 'down' ? 'var(--accent-danger)' : 'var(--accent-success)'} 
                  />
                </div>
              )}
            </div>
            
            <EdgeControls data={data} />
            <SpectrumAnalyzer source={data.source} target={data.target} />
          </>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value, highlight, color, icon }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem' }}>
      <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
        {icon}
        {label}
      </span>
      <span style={{ 
        fontWeight: 600, 
        color: color || (highlight ? 'var(--accent)' : 'var(--text-main)') 
      }}>
        {value}
      </span>
    </div>
  );
}

function EdgeControls({ data }) {
  const [loading, setLoading] = React.useState(false);
  const isDown = data.status === 'down';

  const handleToggle = async () => {
    setLoading(true);
    const endpoint = isDown ? '/api/restore' : '/api/cut';
    try {
      await fetch(`http://localhost:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: data.source, target: data.target })
      });
    } catch (e) {
      console.error(e);
      alert("Error conectando al puente SDN en el puerto 5000");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '1.2rem', display: 'flex', gap: '10px' }}>
      <button 
        onClick={handleToggle}
        disabled={loading}
        style={{
          flex: 1,
          padding: '0.8rem',
          borderRadius: '8px',
          border: 'none',
          background: isDown ? 'var(--accent-success)' : 'var(--accent-danger)',
          color: 'white',
          fontWeight: 'bold',
          cursor: loading ? 'wait' : 'pointer',
          transition: 'all 0.2s ease',
          boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
          opacity: loading ? 0.7 : 1
        }}
      >
        {loading ? 'Procesando...' : (isDown ? 'Restaurar Fibra' : 'Simular Corte de Fibra')}
      </button>
    </div>
  );
}

function OnosMetrics({ nodeId }) {
  const [metrics, setMetrics] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let mounted = true;
    
    const fetchMetrics = async () => {
      setLoading(true);
      try {
        const authHeader = {
          'Authorization': 'Basic ' + btoa('onos:rocks')
        };
        // 1. Encontrar el Device ID real de ONOS
        // Para la Fase 2, ROADM-1 mapea a netconf:10.42.0.1:11001
        const nodeIdNumber = nodeId.split('-')[1];
        const targetAnnotationName = `netconf:10.42.0.1:1100${nodeIdNumber}`;
        
        const resDevices = await fetch('/onos/api/devices', { headers: authHeader });
        const dataDevices = await resDevices.json();
        const device = dataDevices.devices.find(d => d.annotations && d.annotations.name === targetAnnotationName);
        
        if (!device) {
          if (mounted) setMetrics({ error: 'Dispositivo no encontrado en ONOS' });
          return;
        }

        const deviceId = device.id;

        // 2. Obtener Puertos
        const resPorts = await fetch(`/onos/api/devices/${deviceId}/ports`, { headers: authHeader });
        const dataPorts = await resPorts.json();
        const opticalPorts = dataPorts.ports.filter(p => p.type === 'och').length;

        // 3. Obtener Flujos (Reglas)
        const resFlows = await fetch(`/onos/api/flows/${deviceId}`, { headers: authHeader });
        const dataFlows = await resFlows.json();
        const activeFlows = dataFlows.flows ? dataFlows.flows.length : 0;

        if (mounted) {
          setMetrics({
            deviceId,
            hardware: device.mfr,
            opticalPorts,
            activeFlows
          });
        }
      } catch (err) {
        console.error(err);
        if (mounted) setMetrics({ error: 'Error de conexión con ONOS' });
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Refrescar cada 5 seg
    
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [nodeId]);

  if (loading && !metrics) return <div style={{marginTop: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem'}}>Cargando métricas de ONOS...</div>;
  if (metrics && metrics.error) return <div style={{marginTop: '1rem', color: 'var(--accent-danger)', fontSize: '0.85rem'}}>{metrics.error}</div>;
  if (!metrics) return null;

  return (
    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed var(--panel-border)' }}>
      <h3 style={{ fontSize: '0.9rem', color: 'var(--accent)', marginBottom: '0.8rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Activity size={16} /> Métricas ONOS en Vivo
      </h3>
      <InfoRow label="Device ID" value={<span style={{fontSize: '0.75rem'}}>{metrics.deviceId}</span>} />
      <InfoRow label="Fabricante" value={metrics.hardware} />
      <InfoRow label="Puertos Ópticos (OCh)" value={metrics.opticalPorts} />
      <InfoRow label="Flujos Instalados" value={metrics.activeFlows} color="#38bdf8" />
    </div>
  );
}

function SpectrumAnalyzer({ source, target }) {
  const [spectrum, setSpectrum] = React.useState(null);
  
  React.useEffect(() => {
    let mounted = true;
    const fetchSpectrum = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/spectrum');
        const data = await res.json();
        if (mounted) {
          const linkId = `${source}-${target}`;
          setSpectrum(data[linkId]);
        }
      } catch (err) {
        console.error("Error al obtener espectro:", err);
      }
    };
    
    fetchSpectrum();
    const interval = setInterval(fetchSpectrum, 2000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [source, target]);

  if (!spectrum) return null;

  // Calcular estadísticas
  const occupiedCount = spectrum.filter(x => x === 1).length;

  return (
    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px dashed var(--panel-border)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.8rem' }}>
        <h3 style={{ fontSize: '0.9rem', color: 'var(--accent)', margin: 0 }}>Uso de Espectro (DWDM)</h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{occupiedCount}/96 Ocupados</span>
      </div>
      
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
        {spectrum.map((isOccupied, idx) => (
          <div 
            key={idx}
            title={`Lambda ${idx + 1}`}
            style={{
              width: '10px', height: '14px',
              backgroundColor: isOccupied ? 'var(--accent-danger)' : 'var(--accent-success)',
              borderRadius: '2px',
              opacity: isOccupied ? 1 : 0.3,
              cursor: 'help'
            }}
          />
        ))}
      </div>
      
      <div style={{ display: 'flex', gap: '1rem', marginTop: '0.8rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '8px', height: '8px', backgroundColor: 'var(--accent-success)', opacity: 0.3, borderRadius: '1px' }}></div>
          Libre
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '8px', height: '8px', backgroundColor: 'var(--accent-danger)', borderRadius: '1px' }}></div>
          Ocupado
        </div>
      </div>
    </div>
  );
}
