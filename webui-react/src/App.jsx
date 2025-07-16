import React, { useState } from 'react';
import { ThemeProvider, CssBaseline, Container, AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import theme from './theme';
import LoginPage from './pages/LoginPage';
import TaskForm from './pages/TaskForm';
import TaskStatus from './pages/TaskStatus';
import TaskHistory from './pages/TaskHistory';

function App() {
  const [auth, setAuth] = useState({ apiKey: '', jwt: '' });
  const [taskId, setTaskId] = useState('');
  const [taskHistory, setTaskHistory] = useState([]);

  const handleTaskSubmit = (id, input) => {
    setTaskId(id);
    setTaskHistory(prev => [
      { id, input, status: 'pending', time: new Date().toLocaleTimeString(), result: '' },
      ...prev
    ]);
  };

  const updateTaskInHistory = (id, status, result) => {
    setTaskHistory(prev => prev.map(t => t.id === id ? { ...t, status, result } : t));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            ReasoningAgent Web UI
          </Typography>
          {auth.jwt || auth.apiKey ? (
            <Button color="inherit" onClick={() => { setAuth({ apiKey: '', jwt: '' }); setTaskId(''); setTaskHistory([]); }}>Logout</Button>
          ) : null}
        </Toolbar>
      </AppBar>
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        {!auth.jwt && !auth.apiKey ? (
          <LoginPage setAuth={setAuth} />
        ) : !taskId ? (
          <>
            <TaskForm auth={auth} onTaskSubmit={handleTaskSubmit} />
            <Box mt={4}>
              <TaskHistory tasks={taskHistory} setTaskId={setTaskId} />
            </Box>
          </>
        ) : (
          <TaskStatus auth={auth} taskId={taskId} updateTaskInHistory={updateTaskInHistory} />
        )}
      </Container>
    </ThemeProvider>
  );
}

export default App;