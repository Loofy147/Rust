from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.orchestrator.core import OrchestratorAI

app = FastAPI(title="Orchestrator-AI Enterprise Platform")

# CORS for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OrchestratorAI instance (singleton for the app)
orchestrator_ai = OrchestratorAI(max_workers=4, project_goal="Automate and scale all agent/data/LLM workflows.")

# --- Routers (to be implemented in app/api/) ---
# from app.api import users, orgs, agents, tasks, orchestrator
# app.include_router(users.router)
# app.include_router(orgs.router)
# app.include_router(agents.router)
# app.include_router(tasks.router)
# app.include_router(orchestrator.router)

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

@app.get("/orchestrator/status", tags=["orchestrator"])
def orchestrator_status():
    return orchestrator_ai.get_status()