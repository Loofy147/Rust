import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from './config';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Button, LinearProgress, Typography, Dialog, DialogTitle, DialogContent, DialogActions, Tabs, Tab, Box, Snackbar, Alert, DialogContentText } from '@mui/material';

function App() {
  const [samples, setSamples] = useState([]);
  const [labels, setLabels] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [user, setUser] = useState(localStorage.getItem('annotator_user') || '');
  const [loginOpen, setLoginOpen] = useState(!user);
  const [usernameInput, setUsernameInput] = useState('');
  const [tab, setTab] = useState(0);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [history, setHistory] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [qaQueue, setQaQueue] = useState([]);
  const [qaActionStatus, setQaActionStatus] = useState('');
  const [qaEdit, setQaEdit] = useState('');
  const [qaFeedback, setQaFeedback] = useState('');

  useEffect(() => {
    if (user) fetchSamples();
    if (user) fetchHistory();
    if (user) fetchReviewQueue();
    if (user) fetchQaQueue();
  }, [user]);

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
    await axios.post(`${API_BASE_URL}/submit_annotation`, { index: idx, label: labels[idx], user });
    setProgress((prev) => prev + 1);
    setSubmitting(false);
    setSamples(samples.filter((s, i) => i !== idx));
  };

  const handleReview = async (idx, status, comment = '') => {
    await axios.post(`${API_BASE_URL}/review_annotation`, { index: idx, status, reviewer: user, comment });
    setSnackbar({ open: true, message: `Annotation ${status}`, severity: status === 'approved' ? 'success' : 'warning' });
    fetchReviewQueue();
  };

  const fetchReviewQueue = async () => {
    const res = await axios.get(`${API_BASE_URL}/review_queue`);
    setReviewQueue(res.data);
  };

  const fetchHistory = async () => {
    // For demo, just use review queue filtered by user
    const res = await axios.get(`${API_BASE_URL}/review_queue`);
    setHistory(res.data.filter(item => item.user === user));
  };

  const fetchQaQueue = async () => {
    const res = await axios.get(`${API_BASE_URL}/hitl_queue`);
    setQaQueue(res.data);
  };

  const handleQaAction = async (task, action) => {
    await axios.post(`${API_BASE_URL}/hitl_qa`, {
      workflow_id: task.workflow_id,
      step: task.step,
      action,
      edited_answer: qaEdit,
      feedback: qaFeedback,
      user
    });
    setQaActionStatus(`Action '${action}' submitted.`);
    setQaEdit('');
    setQaFeedback('');
    fetchQaQueue();
  };

  const handleLogin = () => {
    if (usernameInput.trim()) {
      setUser(usernameInput.trim());
      localStorage.setItem('annotator_user', usernameInput.trim());
      setLoginOpen(false);
    }
  };

  return (
    <div style={{ padding: 32 }}>
      <Dialog open={loginOpen} disableEscapeKeyDown>
        <DialogTitle>Login</DialogTitle>
        <DialogContent>
          <TextField label="Username" value={usernameInput} onChange={e => setUsernameInput(e.target.value)} autoFocus fullWidth />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleLogin} variant="contained">Login</Button>
        </DialogActions>
      </Dialog>
      <Typography variant="h4" gutterBottom>Annotation UI</Typography>
      <Typography variant="subtitle1" gutterBottom>Current user: <b>{user}</b></Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} style={{ marginBottom: 16 }}>
        <Tab label="Annotate" />
        <Tab label="Review" />
        <Tab label="History/Undo" />
        <Tab label="LLM QA" />
      </Tabs>
      {tab === 0 && (
        <>
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
        </>
      )}
      {tab === 1 && (
        <Box>
          <Typography variant="h6">Review Queue</Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Index</TableCell>
                  <TableCell>Label</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reviewQueue.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{item.index}</TableCell>
                    <TableCell>{item.label}</TableCell>
                    <TableCell>{item.user}</TableCell>
                    <TableCell>{item.status}</TableCell>
                    <TableCell>
                      <Button size="small" color="success" onClick={() => handleReview(item.index, 'approved')}>Approve</Button>
                      <Button size="small" color="error" onClick={() => handleReview(item.index, 'rejected')}>Reject</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
      {tab === 2 && (
        <Box>
          <Typography variant="h6">Annotation History</Typography>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Index</TableCell>
                  <TableCell>Label</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Undo</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{item.index}</TableCell>
                    <TableCell>{item.label}</TableCell>
                    <TableCell>{item.status}</TableCell>
                    <TableCell>
                      <Button size="small" color="warning" onClick={() => handleReview(item.index, 'undone')}>Undo</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
      {tab === 3 && (
        <Box>
          <Typography variant="h6">LLM QA Queue</Typography>
          {qaQueue.length === 0 && <Typography>No pending QA tasks.</Typography>}
          {qaQueue.map((task, idx) => (
            <Paper key={idx} style={{ margin: 16, padding: 16 }}>
              <Typography><b>Question:</b> {task.question || task.llm_output?.question}</Typography>
              <Typography><b>LLM Answer:</b> {task.llm_output?.answer}</Typography>
              <Typography><b>Rationale:</b> {task.llm_output?.rationale}</Typography>
              <Typography><b>Context:</b> <DialogContentText style={{ whiteSpace: 'pre-wrap' }}>{task.context}</DialogContentText></Typography>
              <TextField label="Edit Answer" fullWidth multiline minRows={2} value={qaEdit} onChange={e => setQaEdit(e.target.value)} style={{ marginTop: 8 }} />
              <TextField label="Feedback/Clarification" fullWidth multiline minRows={2} value={qaFeedback} onChange={e => setQaFeedback(e.target.value)} style={{ marginTop: 8 }} />
              <Box style={{ marginTop: 8 }}>
                <Button variant="contained" color="success" onClick={() => handleQaAction(task, 'approve')}>Approve</Button>
                <Button variant="contained" color="warning" onClick={() => handleQaAction(task, 'edit')}>Edit & Approve</Button>
                <Button variant="contained" color="error" onClick={() => handleQaAction(task, 'reject')}>Reject</Button>
              </Box>
            </Paper>
          ))}
          {qaActionStatus && <Alert severity="info" style={{ marginTop: 8 }}>{qaActionStatus}</Alert>}
        </Box>
      )}
      <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })}>
        <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
      </Snackbar>
    </div>
  );
}

export default App;