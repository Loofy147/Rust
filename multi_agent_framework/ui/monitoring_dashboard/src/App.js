import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from './config';
import { AppBar, Toolbar, Typography, Box, Paper, Grid, Alert, CircularProgress } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

function parsePrometheusMetrics(metricsText) {
  const lines = metricsText.split('\n');
  const metrics = {};
  lines.forEach(line => {
    if (line.startsWith('#') || !line.trim()) return;
    const [key, value] = line.split(' ');
    if (!metrics[key]) metrics[key] = [];
    metrics[key].push(parseFloat(value));
  });
  return metrics;
}

function App() {
  const [metrics, setMetrics] = useState({});
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [metricsRes, healthRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/metrics`),
        axios.get(`${API_BASE_URL}/health`)
      ]);
      setMetrics(parsePrometheusMetrics(metricsRes.data));
      setHealth(healthRes.data);
      setError('');
    } catch (err) {
      setError('Failed to fetch metrics or health');
    }
    setLoading(false);
  };

  // Example: extract some metrics
  const apiRequests = metrics['api_requests_total'] || [];
  const apiErrors = metrics['api_errors_total'] || [];
  const agentTasks = metrics['agent_tasks_total'] || [];
  const agentErrors = metrics['agent_errors_total'] || [];
  const workflowDurations = metrics['workflow_duration_seconds'] || [];

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">Monitoring Dashboard</Typography>
        </Toolbar>
      </AppBar>
      <Box p={2}>
        {error && <Alert severity="error">{error}</Alert>}
        {loading && <CircularProgress />}
        {health && health.status !== 'ok' && <Alert severity="warning">System not healthy!</Alert>}
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} style={{ padding: 16 }}>
              <Typography variant="h6">API Requests</Typography>
              <Typography>Total: {apiRequests.reduce((a, b) => a + b, 0)}</Typography>
              <Typography>Errors: {apiErrors.reduce((a, b) => a + b, 0)}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} style={{ padding: 16 }}>
              <Typography variant="h6">Agent Tasks</Typography>
              <Typography>Total: {agentTasks.reduce((a, b) => a + b, 0)}</Typography>
              <Typography>Errors: {agentErrors.reduce((a, b) => a + b, 0)}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} style={{ padding: 16 }}>
              <Typography variant="h6">Workflow Durations (s)</Typography>
              <BarChart width={300} height={150} data={workflowDurations.map((v, i) => ({ name: `Run ${i+1}`, duration: v }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="duration" fill="#8884d8" />
              </BarChart>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}

export default App;