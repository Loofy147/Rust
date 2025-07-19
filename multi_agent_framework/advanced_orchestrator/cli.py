import argparse
import requests
import yaml
import os

API_URL = os.environ.get("ORCH_API_URL", "http://localhost:8000")

parser = argparse.ArgumentParser(description="Orchestrator CLI Utility")
subparsers = parser.add_subparsers(dest="command")

subparsers.add_parser("list-agents", help="List all registered agents")
subparsers.add_parser("list-workflows", help="List all workflows")

register_agent_parser = subparsers.add_parser("register-agent",
                                            help="Register a new agent")
register_agent_parser.add_argument("agent_id")
register_agent_parser.add_argument("skills", nargs="*", default=[])

submit_workflow_parser = subparsers.add_parser("submit-workflow",
                                             help="Submit a workflow from YAML file")
submit_workflow_parser.add_argument("workflow_file")

subparsers.add_parser("diagnostics", help="Show orchestrator diagnostics")

args = parser.parse_args()

if args.command == "list-agents":
    r = requests.get(f"{API_URL}/agents")
    print(r.json())
elif args.command == "list-workflows":
    # This would require an endpoint for workflows
    print("Not implemented: list-workflows endpoint")
elif args.command == "register-agent":
    payload = {"agent_id": args.agent_id, "info": {"skills": args.skills}}
    r = requests.post(f"{API_URL}/register_agent", json=payload)
    print(r.json())
elif args.command == "submit-workflow":
    with open(args.workflow_file, "r") as f:
        wf = yaml.safe_load(f)
    r = requests.post(f"{API_URL}/submit_workflow", json=wf)
    print(r.json())
elif args.command == "diagnostics":
    print("Diagnostics:")
    r = requests.get(f"{API_URL}/agents")
    print("Agents:", r.json())
    # Add more diagnostics as needed
else:
    parser.print_help()
