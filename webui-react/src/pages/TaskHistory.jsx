import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Chip, Button, Dialog, DialogTitle, DialogContent, Typography } from '@mui/material';

const statusColor = status => {
  if (status === 'completed') return 'success';
  if (status === 'failed') return 'error';
  return 'info';
};

function TaskHistory({ tasks, setTaskId }) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(null);

  const handleOpen = task => { setSelected(task); setOpen(true); };
  const handleClose = () => setOpen(false);

  if (!tasks.length) return null;

  return (
    <>
      <Typography variant="h6" mb={2}>Task History</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Time</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map(task => (
              <TableRow key={task.id}>
                <TableCell sx={{ maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis' }}>{task.id.slice(0, 8)}...</TableCell>
                <TableCell><Chip label={task.status || 'pending'} color={statusColor(task.status)} size="small" /></TableCell>
                <TableCell>{task.time}</TableCell>
                <TableCell>
                  <Button size="small" onClick={() => setTaskId(task.id)}>View</Button>
                  <Button size="small" onClick={() => handleOpen(task)}>Details</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Task Details</DialogTitle>
        <DialogContent>
          {selected && (
            <>
              <Typography variant="subtitle2">ID:</Typography>
              <Typography mb={1}>{selected.id}</Typography>
              <Typography variant="subtitle2">Status:</Typography>
              <Typography mb={1}>{selected.status}</Typography>
              <Typography variant="subtitle2">Time:</Typography>
              <Typography mb={1}>{selected.time}</Typography>
              <Typography variant="subtitle2">Input:</Typography>
              <Typography mb={1} sx={{ whiteSpace: 'pre-wrap' }}>{selected.input}</Typography>
              <Typography variant="subtitle2">Result/Error:</Typography>
              <Typography mb={1} sx={{ whiteSpace: 'pre-wrap' }}>{selected.result}</Typography>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

export default TaskHistory;