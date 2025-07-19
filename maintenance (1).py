
"""
maintenance.py

Comprehensive script to organize, update, improve, and refactor the Integrated AI Platform.
Features:
- Syntax error correction using ErrorCorrectionAgent
- Dynamic optimization via AgentOptimizer
- System health checks via SystemHarmonyAgent
- Code formatting and linting (black, flake8)
- Automated testing (pytest)
- Service orchestration (start/stop FastAPI services)
- KG embedding demo (PyKEEN)
- Optional ngrok tunneling setup
"""

import os
import subprocess
import sys
import asyncio

# Ensure project src path is on PYTHONPATH
sys.path.append(os.path.abspath("src"))

from agents.error_correction_agent import ErrorCorrectionAgent
from agents.agent_optimizer import AgentOptimizer
from agents.system_harmony_agent import SystemHarmonyAgent
from integration.integration_orchestrator import IntegratedOrchestrator

# Configuration
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
GENERATED_DIR = os.path.join(SRC_DIR, "agents", "generated")

def fix_errors():
    print("Running syntax error correction...")
    agent = ErrorCorrectionAgent(source_dir=SRC_DIR)
    agent.initialize()
    report = agent.handle()
    print("Error correction report:", report)
    agent.shutdown()

def optimize_agents():
    print("Running dynamic optimization of agents...")
    harmony = SystemHarmonyAgent()
    harmony.initialize()
    result = harmony.handle({"mode": "optimize"})
    print("Optimization cycles:", result)
    harmony.shutdown()

def health_check():
    print("Performing system health check...")
    harmony = SystemHarmonyAgent()
    harmony.initialize()
    health = harmony.handle({"mode": "health"})
    print("Health report:", health)
    harmony.shutdown()

def run_format_and_lint():
    print("Formatting code with black and checking with flake8...")
    subprocess.run([sys.executable, "-m", "black", SRC_DIR, "--line-length", "88"], check=False)
    subprocess.run([sys.executable, "-m", "flake8", SRC_DIR], check=False)

def run_tests():
    print("Running pytest suite...")
    subprocess.run([sys.executable, "-m", "pytest", "-q", "--disable-warnings", "--maxfail=1"], check=False)

def start_services():
    print("Starting FastAPI services...")
    subprocess.Popen(["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
    subprocess.Popen(["uvicorn", "src.ui_agents:app", "--host", "0.0.0.0", "--port", "8001", "--reload"])
    subprocess.Popen(["uvicorn", "src/multimodal_interaction_agent:app", "--host", "0.0.0.0", "--port", "8002", "--reload"])
    print("Services started on ports 8000, 8001, 8002")

def run_embedding_demo():
    try:
        from pykeen.pipeline import pipeline
        print("Running KG embedding demo (TransE on nations)...")
        result = pipeline(
            dataset='nations',
            model='TransE',
            training_kwargs=dict(num_epochs=3),
        )
        print("Embedding metrics:", result.metric_results.to_flat_dict())
    except ImportError:
        print("pykeen not installed. Skipping embedding demo.")

def main():
    fix_errors()
    optimize_agents()
    health_check()
    run_format_and_lint()
    run_tests()
    run_embedding_demo()
    start_services()

if __name__ == "__main__":
    main()
