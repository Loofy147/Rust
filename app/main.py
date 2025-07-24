from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.orchestrator.core import OrchestratorAI
from app.api import users, orgs, agents, tasks, orchestrator

# --- Advanced agent modules ---
from super_advanced_agents import (
    FAISSVectorStore, EmbeddingPipeline, LLMGenerator,
    RetrieverAgent, SummarizerAgent, ConversationalAgent, TrainingDataAgent
)

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
orchestrator_ai = OrchestratorAI(project_goal="Automate and scale all agent/data/LLM workflows.")

@app.on_event("startup")
async def startup_event():
    await orchestrator_ai.setup()

@app.on_event("shutdown")
async def shutdown_event():
    await orchestrator_ai.stop()

# --- Instantiate and register advanced agents ---
store = FAISSVectorStore(dim=384)
embedder = EmbeddingPipeline()
llm = LLMGenerator()
retriever = RetrieverAgent("Retriever", store, embedder, llm)
summarizer = SummarizerAgent("Summarizer", store, embedder, llm)
conversational = ConversationalAgent("Conversational", store, embedder, llm)
training = TrainingDataAgent(store, embedder)

orchestrator_ai.register_agent("retriever", retriever)
orchestrator_ai.register_agent("summarizer", summarizer)
orchestrator_ai.register_agent("conversational", conversational)
orchestrator_ai.register_agent("training", training)

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