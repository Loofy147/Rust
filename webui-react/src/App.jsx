import React, { useState } from 'react';
import { ThemeProvider, CssBaseline, Container, AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import theme from './theme';
import LoginPage from './pages/LoginPage';
import TaskForm from './pages/TaskForm';
import TaskStatus from './pages/TaskStatus';

function App() {
  const [auth, setAuth] = useState({ apiKey: '', jwt: '' });
  const [taskId, setTaskId] = useState('');

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            ReasoningAgent Web UI
          </Typography>
          {auth.jwt || auth.apiKey ? (
            <Button color="inherit" onClick={() => { setAuth({ apiKey: '', jwt: '' }); setTaskId(''); }}>Logout</Button>
          ) : null}
        </Toolbar>
      </AppBar>
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        {!auth.jwt && !auth.apiKey ? (
          <LoginPage setAuth={setAuth} />
        ) : !taskId ? (
          <TaskForm auth={auth} setTaskId={setTaskId} />
        ) : (
          <TaskStatus auth={auth} taskId={taskId} />
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;