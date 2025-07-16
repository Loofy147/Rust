import React, { useState } from 'react';
import { Box, TextField, Button, Alert, Typography } from '@mui/material';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function TaskForm({ auth, setTaskId }) {
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const headers = {};
  if (auth.apiKey) headers['x-api-key'] = auth.apiKey;
  if (auth.jwt) headers['Authorization'] = `Bearer ${auth.jwt}`;

  const handleSubmit = async () => {
    setError(''); setSuccess(''); setLoading(true);
    try {
      const resp = await axios.post(`${API_URL}/tasks`, { input }, { headers });
      setTaskId(resp.data.id);
      setSuccess(`Task submitted! Task ID: ${resp.data.id}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" mb={2}>Submit a Task</Typography>
      <TextField
        label="Task Input"
        multiline
        minRows={3}
        maxRows={8}
        fullWidth
        value={input}
        onChange={e => setInput(e.target.value)}
        inputProps={{ maxLength: 2048 }}
        sx={{ mb: 2 }}
      />
      <Button variant="contained" fullWidth onClick={handleSubmit} disabled={loading || !input.trim()}>
        {loading ? 'Submitting...' : 'Submit Task'}
      </Button>
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mt: 2 }}>{success}</Alert>}
    </Box>
  );
}

export default TaskForm;