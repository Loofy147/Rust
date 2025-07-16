import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from './config';
import { AppBar, Toolbar, Typography, Box, Paper, Grid, Alert, CircularProgress, Dialog, DialogTitle, DialogContent, Button, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material';
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
  const [workflowModalOpen, setWorkflowModalOpen] = useState(false);
  const [workflowHistory, setWorkflowHistory] = useState({ history: [], feedback: [] });
  const [agentModalOpen, setAgentModalOpen] = useState(false);
  const [agentLogs, setAgentLogs] = useState([]);
  const [userAnalytics, setUserAnalytics] = useState([]);

  useEffect(() => {
    fetchAll();
    fetchUserAnalytics();
    const interval = setInterval(() => { fetchAll(); fetchUserAnalytics(); }, 5000);
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

  const fetchWorkflowHistory = async (workflowId) => {
    const res = await axios.get(`${API_BASE_URL}/workflow_history/${workflowId}`);
    setWorkflowHistory(res.data);
    setWorkflowModalOpen(true);
  };

  const fetchAgentLogs = async (agentId) => {
    const res = await axios.get(`${API_BASE_URL}/agent_logs/${agentId}`);
    setAgentLogs(res.data.logs);
    setAgentModalOpen(true);
  };

  const fetchUserAnalytics = async () => {
    const res = await axios.get(`${API_BASE_URL}/user_analytics`);
    setUserAnalytics(res.data.leaderboard);
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
              <Button onClick={() => fetchAgentLogs('agent_id_example')}>Drill Down</Button>
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
              <Button onClick={() => fetchWorkflowHistory('workflow_id_example')}>Drill Down</Button>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper elevation={2} style={{ padding: 16 }}>
              <Typography variant="h6">User Analytics</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>User</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {userAnalytics.map(([user, count], idx) => (
                    <TableRow key={idx}>
                      <TableCell>{user}</TableCell>
                      <TableCell>{count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>
        </Grid>
        {/* Workflow Drill-down Modal */}
        <Dialog open={workflowModalOpen} onClose={() => setWorkflowModalOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Workflow Run History</DialogTitle>
          <DialogContent>
            <Typography variant="subtitle1">History</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Step</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Output</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {workflowHistory.history.map((h, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{h.step_id}</TableCell>
                    <TableCell>{h.status}</TableCell>
                    <TableCell>{new Date(h.timestamp * 1000).toLocaleString()}</TableCell>
                    <TableCell><pre style={{ maxWidth: 200, overflow: 'auto' }}>{JSON.stringify(h.output, null, 2)}</pre></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Typography variant="subtitle1" style={{ marginTop: 16 }}>Feedback</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Step</TableCell>
                  <TableCell>Feedback</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {workflowHistory.feedback.map((f, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{f.step_id}</TableCell>
                    <TableCell><pre style={{ maxWidth: 300, overflow: 'auto' }}>{JSON.stringify(f.feedback, null, 2)}</pre></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </DialogContent>
        </Dialog>
        {/* Agent Drill-down Modal */}
        <Dialog open={agentModalOpen} onClose={() => setAgentModalOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Agent Logs</DialogTitle>
          <DialogContent>
            <pre style={{ maxHeight: 400, overflow: 'auto' }}>{JSON.stringify(agentLogs, null, 2)}</pre>
          </DialogContent>
        </Dialog>
      </Box>
    </Box>
  );
}

export default App;