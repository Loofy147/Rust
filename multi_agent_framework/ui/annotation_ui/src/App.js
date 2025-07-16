import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from './config';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Button, LinearProgress, Typography } from '@mui/material';

function App() {
  const [samples, setSamples] = useState([]);
  const [labels, setLabels] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    fetchSamples();
  }, []);

  const fetchSamples = async () => {
    const res = await axios.get(`${API_BASE_URL}/annotation_samples`);
    setSamples(res.data);
    setProgress(0);
    setLabels({});
  };

  const handleLabelChange = (idx, value) => {
    setLabels({ ...labels, [idx]: value });
  };

  const handleSubmit = async (idx) => {
    setSubmitting(true);
    await axios.post(`${API_BASE_URL}/submit_annotation`, { index: idx, label: labels[idx] });
    setProgress((prev) => prev + 1);
    setSubmitting(false);
    // Optionally, remove annotated sample from UI
    setSamples(samples.filter((s, i) => i !== idx));
  };

  return (
    <div style={{ padding: 32 }}>
      <Typography variant="h4" gutterBottom>Annotation UI</Typography>
      <LinearProgress variant="determinate" value={samples.length === 0 ? 100 : (progress / samples.length) * 100} style={{ marginBottom: 16 }} />
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {samples[0] && Object.keys(samples[0]).map((col) => (
                <TableCell key={col}>{col}</TableCell>
              ))}
              <TableCell>Label</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {samples.map((row, idx) => (
              <TableRow key={idx}>
                {Object.values(row).map((val, i) => (
                  <TableCell key={i}>{val}</TableCell>
                ))}
                <TableCell>
                  <TextField size="small" value={labels[idx] || ''} onChange={e => handleLabelChange(idx, e.target.value)} />
                </TableCell>
                <TableCell>
                  <Button variant="contained" size="small" disabled={submitting || !labels[idx]} onClick={() => handleSubmit(idx)}>Submit</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Button variant="outlined" style={{ marginTop: 16 }} onClick={fetchSamples}>Refresh</Button>
    </div>
  );
}

export default App;