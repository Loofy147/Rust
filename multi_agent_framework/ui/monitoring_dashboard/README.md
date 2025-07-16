# Monitoring Dashboard

A real-time dashboard for system, workflow, agent, and HITL analytics.

## Features
- System health: uptime, error rates, latency
- Workflow analytics: runs, success/failure, duration
- Agent analytics: task counts, errors, status
- HITL analytics: interventions, approval/rejection rates
- LLM/retrieval analytics: query volume, feedback
- Real-time updates and drill-down
- Alert banners for critical issues

## Setup

```
cd ui/monitoring_dashboard
npm install
npm start
```

## Configuration
- API base URL is set in `src/config.js` (default: `http://localhost:8000`)

## Usage
- View system and workflow health, drill down to details, and monitor HITL activity.