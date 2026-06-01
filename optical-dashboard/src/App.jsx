import React, { useState } from 'react';
import Header from './components/Header';
import TopologyGraph from './components/TopologyGraph';
import SidePanel from './components/SidePanel';
import topologyData from './topology.json';

function App() {
  const [selectedElement, setSelectedElement] = useState(null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      <Header />
      
      <main style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <TopologyGraph 
            data={topologyData} 
            onElementSelect={setSelectedElement} 
          />
        </div>
        
        <SidePanel element={selectedElement} />
      </main>
    </div>
  );
}

export default App;
