import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, Alert, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function TaskStatus({ auth, taskId, updateTaskInHistory }) {
  const [status, setStatus] = useState('pending');
  const [result, setResult] = useState('');
  const [error, setError] = useState('');
  const wsRef = useRef(null);

  const headers = {};
  if (auth.apiKey) headers['x-api-key'] = auth.apiKey;
  if (auth.jwt) headers['Authorization'] = `Bearer ${auth.jwt}`;

  useEffect(() => {
    let active = true;
    setError('');
    setStatus('pending');
    setResult('');
    // Try WebSocket first
    const wsUrl = API_URL.replace('http', 'ws') + `/ws/tasks/${taskId}`;
    try {
      wsRef.current = new window.WebSocket(wsUrl);
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.error) {
          setError(data.error);
          wsRef.current.close();
          updateTaskInHistory(taskId, 'failed', data.error);
          return;
        }
        setStatus(data.status);
        if (data.result) setResult(data.result);
        updateTaskInHistory(taskId, data.status, data.result || '');
      };
      wsRef.current.onerror = () => {
        wsRef.current.close();
        pollStatus();
      };
      wsRef.current.onclose = () => {
        if (status !== 'completed' && status !== 'failed') pollStatus();
      };
    } catch (e) {
      pollStatus();
    }
    function pollStatus() {
      if (!active) return;
      axios.get(`${API_URL}/tasks/${taskId}`, { headers })
        .then(resp => {
          setStatus(resp.data.status);
          if (resp.data.result) setResult(resp.data.result);
          updateTaskInHistory(taskId, resp.data.status, resp.data.result || '');
          if (!resp.data.result && active) setTimeout(pollStatus, 2000);
        })
        .catch(e => setError('Polling failed'));
    }
    return () => { active = false; wsRef.current?.close(); };
    // eslint-disable-next-line
  }, [taskId]);

  return (
    <Box>
      <Typography variant="h5" mb={2}>Task Status</Typography>
      <Typography variant="body1" mb={2}>Task ID: {taskId}</Typography>
      {error && <Alert severity="error">{error}</Alert>}
      <Alert severity={status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'info'} sx={{ mb: 2 }}>
        Status: {status}
      </Alert>
      {status === 'pending' && <CircularProgress />}
      {result && (
        <Box mt={2}>
          <Typography variant="subtitle1">Result:</Typography>
          <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>{result}</pre>
        </Box>
      )}
      <Button variant="outlined" sx={{ mt: 2 }} onClick={() => updateTaskInHistory(taskId, '', '')}>Submit Another Task</Button>
    </Box>
  );
}

export default TaskStatus;