import requests
import time

def test_event_sourcing():
    # Register agent and check event store (assumes local orchestrator)
    r = requests.post('http://localhost:8000/register_agent', json={"agent_id": "test_agent", "info": {"skills": ["test"]}})
    assert r.status_code == 200
    # Event store is in-memory; check via orchestrator or logs


def test_hitl_approval():
    # Submit workflow with HITL step
    steps = [
        {"id": "s1", "label": "step1"},
        {"id": "s2", "label": "step2", "hitl": True, "depends_on": ["s1"]}
    ]
    r = requests.post('http://localhost:8000/submit_workflow', json={"workflow_id": "wf1", "steps": steps, "dag": True})
    assert r.status_code == 200
    # Approve HITL step
    r2 = requests.post('http://localhost:8000/approve_hitl_step', json={"workflow_id": "wf1", "step_id": "s2"})
    assert r2.status_code == 200


def test_edge_agent_registration():
    r = requests.post('http://localhost:8000/register_edge_agent', json={"agent_id": "edge1", "info": {"skills": ["edge"]}, "edge_location": "siteA"})
    assert r.status_code == 200
    r2 = requests.get('http://localhost:8000/edge_agents?location=siteA')
    assert r2.status_code == 200
    assert "edge1" in r2.json()


def test_plugin_marketplace():
    r = requests.get('http://localhost:8000/plugins')
    assert r.status_code == 200
    r2 = requests.get('http://localhost:8000/workflows')
    assert r2.status_code == 200