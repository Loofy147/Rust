# Advanced Annotation UI

A web-based, human-in-the-loop annotation interface for the multi-agent orchestration platform.

## Features
- Fetches samples needing annotation from orchestrator API
- Displays data in a paginated table
- Allows users to input/select labels
- Submits labels via API
- Shows annotation progress and status
- Supports batch annotation and review

## Setup

```
cd ui/annotation_ui
npm install
npm start
```

## Configuration
- API base URL is set in `src/config.js` (default: `http://localhost:8000`)

## Usage
- Annotate samples, submit labels, and track progress in the UI.