import React, { useState } from 'react';
import { Box, TextField, Button, Typography, ToggleButton, ToggleButtonGroup, Alert } from '@mui/material';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function LoginPage({ setAuth }) {
  const [authMethod, setAuthMethod] = useState('apikey');
  const [apiKey, setApiKey] = useState('');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async () => {
    setError('');
    if (authMethod === 'apikey') {
      if (!apiKey) return setError('API key required');
      setAuth({ apiKey, jwt: '' });
    } else {
      try {
        const resp = await axios.post(`${API_URL}/token`, new URLSearchParams({ username, password }));
        setAuth({ apiKey: '', jwt: resp.data.access_token });
      } catch (e) {
        setError('Login failed');
      }
    }
  };

  return (
    <Box>
      <Typography variant="h5" mb={2}>Login</Typography>
      <ToggleButtonGroup
        value={authMethod}
        exclusive
        onChange={(_, v) => v && setAuthMethod(v)}
        sx={{ mb: 2 }}
      >
        <ToggleButton value="apikey">API Key</ToggleButton>
        <ToggleButton value="jwt">JWT Login</ToggleButton>
      </ToggleButtonGroup>
      {authMethod === 'apikey' ? (
        <TextField
          label="API Key"
          type="password"
          fullWidth
          value={apiKey}
          onChange={e => setApiKey(e.target.value)}
          sx={{ mb: 2 }}
        />
      ) : (
        <>
          <TextField
            label="Username"
            fullWidth
            value={username}
            onChange={e => setUsername(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            value={password}
            onChange={e => setPassword(e.target.value)}
            sx={{ mb: 2 }}
          />
        </>
      )}
      <Button variant="contained" fullWidth onClick={handleLogin}>Login</Button>
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
    </Box>
  );
}

export default LoginPage;