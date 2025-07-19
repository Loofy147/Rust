from fastapi import FastAPI
from autonomous_architect.orchestrator import AutonomousArchitectureOrchestrator
from autonomous_architect.config import default_config
import asyncio

app = FastAPI()
orchestrator = AutonomousArchitectureOrchestrator(default_config)

@app.get("/status")
def status():
    return {"agents": [a.agent_id for a in orchestrator.agents]}

@app.post("/trigger_analysis")
async def trigger_analysis():
    await orchestrator.run_ml_analysis()
    return {"status": "analysis complete"}

@app.get("/ml_insights")
def ml_insights():
    graph = orchestrator.codebase_graph.graph
    patterns = orchestrator.pattern_recognizer.mine_patterns(graph)
    anomalies = orchestrator.pattern_recognizer.detect_anomalies(graph)
    prediction = orchestrator.predictive_analytics.predict_issues(graph, history=None, anomalies=anomalies)
    recommendation = orchestrator.predictive_analytics.recommend_evolution(graph, patterns=patterns)
    return {
        "patterns": patterns,
        "anomalies": anomalies,
        "prediction": prediction,
        "recommendation": recommendation
    }