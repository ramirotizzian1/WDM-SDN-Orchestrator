import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

export default function TopologyGraph({ data, onElementSelect }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const nodesDataSetRef = useRef(null);
  const edgesDataSetRef = useRef(null);

  // 1. Inicialización de la red (se ejecuta solo una vez cuando carga la data)
  useEffect(() => {
    if (!containerRef.current || !data) return;

    // Crear DataSets para poder actualizarlos en vivo sin re-renderizar
    const nodes = new DataSet(
      data.nodes.map((n) => ({
        id: n.id,
        label: n.id,
        title: `Location: ${n.location}`,
        shape: 'hexagon',
        size: 35,
        color: {
          background: '#1e293b',
          border: '#38bdf8',
          highlight: { background: '#0f172a', border: '#7dd3fc' }
        },
        font: { color: '#f8fafc', face: 'Inter', size: 14 },
        borderWidth: 2,
        shadow: { enabled: true, color: 'rgba(56, 189, 248, 0.4)', size: 10, x: 0, y: 0 },
        _data: n
      }))
    );

    const edges = new DataSet(
      data.links.map((l) => ({
        id: l.id || `link-${l.source}-${l.target}`,
        from: l.source,
        to: l.target,
        label: `${l.length_km} km`,
        font: { align: 'top', color: '#94a3b8', strokeWidth: 0, face: 'Inter', size: 12 },
        color: { 
          color: l.status === 'down' ? '#ef4444' : '#64748b', 
          highlight: l.status === 'down' ? '#f87171' : '#38bdf8' 
        },
        width: 3,
        dashes: l.status === 'down' ? [5, 5] : false,
        smooth: { type: 'continuous' },
        _data: l
      }))
    );

    nodesDataSetRef.current = nodes;
    edgesDataSetRef.current = edges;

    const graphData = { nodes, edges };

    const options = {
      physics: {
        stabilization: true,
        barnesHut: {
          gravitationalConstant: -2000,
          springConstant: 0.04,
          springLength: 250
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true
      }
    };

    networkRef.current = new Network(containerRef.current, graphData, options);

    // Eventos
    networkRef.current.on('selectNode', (params) => {
      const nodeId = params.nodes[0];
      const nodeObj = nodesDataSetRef.current.get(nodeId);
      if (nodeObj) {
        onElementSelect({ type: 'node', data: nodeObj._data });
      }
    });

    networkRef.current.on('selectEdge', (params) => {
      if (params.nodes.length > 0) return;
      const edgeId = params.edges[0];
      const edgeObj = edgesDataSetRef.current.get(edgeId);
      if (edgeObj) {
        onElementSelect({ type: 'edge', data: edgeObj._data });
      }
    });

    networkRef.current.on('deselectNode', () => {
      if (networkRef.current.getSelectedEdges().length === 0) {
        onElementSelect(null);
      }
    });

    networkRef.current.on('deselectEdge', () => {
      if (networkRef.current.getSelectedNodes().length === 0) {
        onElementSelect(null);
      }
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, []); // El array vacío evita que se recargue toda la red

  // 2. Polling hacia ONOS usando el proxy
  useEffect(() => {
    const fetchOnosData = async () => {
      try {
        // Fetch devices (ROADMs)
        const resDevices = await fetch('/onos/api/devices');
        if (!resDevices.ok) throw new Error('Network response from ONOS was not ok');
        const devicesData = await resDevices.json();
        
        // Mapear el estado a los nodos
        if (nodesDataSetRef.current) {
          const currentNodes = nodesDataSetRef.current.get();
          
          currentNodes.forEach(node => {
            // Buscar el nodo en la respuesta de ONOS
            // ONOS devuelve en annotations.name el ID que usamos (ej: "ROADM-1")
            const onosDevice = devicesData.devices.find(d => 
              d.annotations && d.annotations.name === node.id
            );

            if (onosDevice) {
              // Si está available, color normal, si no, color rojo de alerta
              const isAvailable = onosDevice.available;
              
              nodesDataSetRef.current.update({
                id: node.id,
                color: {
                  background: isAvailable ? '#1e293b' : '#ef4444',
                  border: isAvailable ? '#38bdf8' : '#dc2626',
                  highlight: { 
                    background: isAvailable ? '#0f172a' : '#b91c1c', 
                    border: isAvailable ? '#7dd3fc' : '#f87171' 
                  }
                },
                shadow: { 
                  enabled: true, 
                  color: isAvailable ? 'rgba(56, 189, 248, 0.4)' : 'rgba(239, 68, 68, 0.6)' 
                }
              });
            }
          });
        }
      } catch (error) {
        console.error("Error fetching data from ONOS:", error);
      }
    };

    // Consultar inmediatamente y luego cada 3 segundos
    fetchOnosData();
    const interval = setInterval(fetchOnosData, 3000);

    return () => clearInterval(interval);
  }, []);

  // 3. Reaccionar a cambios en data (HMR de Vite al editar topology.json)
  useEffect(() => {
    if (!data || !edgesDataSetRef.current) return;
    
    // Convertir el active_path en un set de identificadores de enlaces (por ej: "ROADM-1-ROADM-2")
    const activePathEdges = new Set();
    if (data.active_path && data.active_path.length > 1) {
      for (let i = 0; i < data.active_path.length - 1; i++) {
        activePathEdges.add(`${data.active_path[i]}-${data.active_path[i+1]}`);
        activePathEdges.add(`${data.active_path[i+1]}-${data.active_path[i]}`);
      }
    }
    
    data.links.forEach(l => {
      const edgeId = l.id || `link-${l.source}-${l.target}`;
      const isPathActive = activePathEdges.has(`${l.source}-${l.target}`);
      const isDown = l.status === 'down';
      
      let baseColor = '#64748b';
      let highlightColor = '#38bdf8';
      let edgeWidth = 3;
      let shadowEffect = false;
      
      if (isDown) {
        baseColor = '#ef4444';
        highlightColor = '#f87171';
      } else if (isPathActive) {
        baseColor = '#06b6d4'; // Cyan neon para lightpath
        highlightColor = '#22d3ee';
        edgeWidth = 6; // Hacemos el enlace activo más grueso
        shadowEffect = { enabled: true, color: '#06b6d4', size: 15, x: 0, y: 0 };
      }

      edgesDataSetRef.current.update({
        id: edgeId,
        color: { 
          color: baseColor, 
          highlight: highlightColor 
        },
        width: edgeWidth,
        dashes: isDown ? [5, 5] : false,
        shadow: shadowEffect,
        _data: l
      });
    });
  }, [data]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%', outline: 'none' }} />
    </div>
  );
}
