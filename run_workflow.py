import requests
import yaml
import logging
import time

logging.basicConfig(level=logging.INFO)

API_URL = "http://localhost:8000"

def submit_workflow(workflow_path):
    logging.info(f"Loading workflow from {workflow_path}")
    with open(workflow_path, 'r') as f:
        workflow = yaml.safe_load(f)

    workflow_id = workflow.get("workflow_id")
    if not workflow_id:
        logging.error("Workflow ID not found in YAML file.")
        return

    logging.info("Submitting workflow to orchestrator...")
    try:
        response = requests.post(f"{API_URL}/submit_workflow", json=workflow, timeout=120)
        response.raise_for_status()
        logging.info("Workflow submitted successfully:")
        logging.info(response.json())
    except requests.exceptions.RequestException as e:
        logging.error(f"Error submitting workflow: {e}")
        return

    time.sleep(5)  # Give the workflow time to run

    logging.info(f"Fetching history for workflow {workflow_id}...")
    try:
        response = requests.get(f"{API_URL}/workflow_history/{workflow_id}", timeout=120)
        response.raise_for_status()
        logging.info("Workflow history:")
        logging.info(response.json())
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching workflow history: {e}")


if __name__ == "__main__":
    submit_workflow("multi_agent_framework/config/advanced_workflow.yaml")
