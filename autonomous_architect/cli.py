import argparse
import asyncio
from autonomous_architect.orchestrator import AutonomousArchitectureOrchestrator
from autonomous_architect.config import default_config

parser = argparse.ArgumentParser(description="Autonomous Architecture Agent CLI")
subparsers = parser.add_subparsers(dest="command")

subparsers.add_parser("run", help="Run the orchestrator event loop")
subparsers.add_parser("analyze", help="Run ML analysis on the codebase graph")

args = parser.parse_args()

orchestrator = AutonomousArchitectureOrchestrator(default_config)

if args.command == "run":
    asyncio.run(orchestrator.start_orchestration())
elif args.command == "analyze":
    asyncio.run(orchestrator.run_ml_analysis())
else:
    parser.print_help()