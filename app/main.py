from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.orchestrator.core import OrchestratorAI
from app.api import users, orgs, agents, tasks, orchestrator

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

# Inject orchestrator_ai into orchestrator router
def set_orchestrator_ai(router, orchestrator_ai):
    import types
    router.orchestrator_ai = orchestrator_ai
    for route in router.routes:
        if hasattr(route.endpoint, "__globals__"):
            route.endpoint.__globals__["orchestrator_ai"] = orchestrator_ai
set_orchestrator_ai(orchestrator.router, orchestrator_ai)

# --- Routers ---
app.include_router(users.router)
app.include_router(orgs.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(orchestrator.router)

@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

@app.get("/orchestrator/status", tags=["orchestrator"])
def orchestrator_status():
    return orchestrator_ai.get_status()