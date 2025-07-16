import React, { useState } from 'react';
import ReactFlow, { MiniMap, Controls, Background } from 'react-flow-renderer';
import { Button, Checkbox, FormControlLabel } from '@mui/material';
import yaml from 'js-yaml';

const initialNodes = [
  { id: '1', data: { label: 'Step 1', hitl: false }, position: { x: 100, y: 100 } },
  { id: '2', data: { label: 'Step 2', hitl: false }, position: { x: 300, y: 100 } },
];
const initialEdges = [
  { id: 'e1-2', source: '1', target: '2' },
];

function App() {
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);

  const handleHitlToggle = (id) => {
    setNodes(nodes.map(n => n.id === id ? { ...n, data: { ...n.data, hitl: !n.data.hitl } } : n));
  };

  const exportYaml = () => {
    const steps = nodes.map(n => ({ id: n.id, label: n.data.label, hitl: n.data.hitl }));
    const dag = true;
    const workflow = { steps, dag };
    const yamlStr = yaml.dump(workflow);
    alert(yamlStr);
  };

  return (
    <div style={{ height: 500 }}>
      <h2>Visual Workflow Builder</h2>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
      <div>
        {nodes.map(n => (
          <FormControlLabel
            key={n.id}
            control={<Checkbox checked={n.data.hitl} onChange={() => handleHitlToggle(n.id)} />}
            label={`HITL: ${n.data.label}`}
          />
        ))}
      </div>
      <Button variant="contained" onClick={exportYaml}>Export as YAML</Button>
    </div>
  );
}

export default App;