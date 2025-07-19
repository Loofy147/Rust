// REST API server for ReasoningAgent
// This demonstrates how to expose the ReasoningAgent through HTTP endpoints

use reasoning_agent::{
    ReasoningAgent,
    plugins::{MockLLMPlugin, DefaultPromptBuilderPlugin},
    knowledge_graph::InMemoryKnowledgeGraph,
    vector_store::InMemoryVectorStore,
    metrics::MetricsCollector,
    types::KnowledgeEntity,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{info, warn, Level};
use tracing_subscriber;

#[derive(Serialize, Deserialize)]
struct TaskRequest {
    task: String,
}

#[derive(Serialize, Deserialize)]
struct TaskResponse {
    result: String,
    duration_ms: u64,
    kg_entities_used: usize,
    similar_vectors_found: usize,
}

#[derive(Serialize, Deserialize)]
struct MetricsResponse {
    uptime_seconds: u64,
    total_tasks_completed: usize,
    success_rate: f64,
    avg_processing_time_ms: f64,
}

#[derive(Serialize, Deserialize)]
struct AddEntityRequest {
    id: String,
    entity_type: String,
    properties: Vec<(String, String)>,
}

type AgentType = Arc<Mutex<ReasoningAgent<
    InMemoryKnowledgeGraph,
    InMemoryVectorStore,
    MockLLMPlugin,
    DefaultPromptBuilderPlugin,
>>>;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();

    info!("Starting ReasoningAgent REST server");

    // Initialize ReasoningAgent
    let knowledge_graph = InMemoryKnowledgeGraph::with_sample_data();
    let vector_store = InMemoryVectorStore::new();
    let metrics_collector = MetricsCollector::new();
    let llm_plugin = Box::new(MockLLMPlugin::new());
    let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

    let agent = Arc::new(Mutex::new(ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics_collector,
    )));

    // Simple HTTP server simulation (in a real implementation, use axum, warp, or actix-web)
    info!("ReasoningAgent REST API would be available at:");
    info!("POST /api/tasks - Submit a task for reasoning");
    info!("GET /api/metrics - Get system metrics");
    info!("POST /api/knowledge - Add knowledge entity");
    info!("GET /api/health - Health check");

    // Simulate some API calls
    simulate_api_calls(agent.clone()).await?;

    Ok(())
}

async fn simulate_api_calls(agent: AgentType) -> anyhow::Result<()> {
    info!("\n=== Simulating REST API calls ===");

    // Simulate POST /api/tasks
    info!("\n1. POST /api/tasks");
    let task_request = TaskRequest {
        task: "What are the economic benefits of wind energy?".to_string(),
    };
    
    let start_time = std::time::Instant::now();
    let result = {
        let mut agent_lock = agent.lock().await;
        agent_lock.process_task(&task_request.task).await?
    };
    let duration = start_time.elapsed();

    let response = TaskResponse {
        result,
        duration_ms: duration.as_millis() as u64,
        kg_entities_used: 3, // Would be actual count from processing
        similar_vectors_found: 5,
    };
    
    info!("Response: {:?}", serde_json::to_string_pretty(&response)?);

    // Simulate GET /api/metrics
    info!("\n2. GET /api/metrics");
    let metrics = {
        let agent_lock = agent.lock().await;
        let system_metrics = agent_lock.get_metrics().get_system_metrics();
        MetricsResponse {
            uptime_seconds: system_metrics.uptime_seconds,
            total_tasks_completed: system_metrics.total_tasks_completed,
            success_rate: system_metrics.success_rate,
            avg_processing_time_ms: system_metrics.avg_processing_time_ms,
        }
    };
    
    info!("Metrics: {:?}", serde_json::to_string_pretty(&metrics)?);

    // Simulate POST /api/knowledge
    info!("\n3. POST /api/knowledge");
    let entity_request = AddEntityRequest {
        id: "offshore_wind_001".to_string(),
        entity_type: "technology".to_string(),
        properties: vec![
            ("name".to_string(), "Offshore Wind Energy".to_string()),
            ("capacity_factor".to_string(), "45-50%".to_string()),
            ("cost_trend".to_string(), "Decreasing due to larger turbines".to_string()),
        ],
    };

    // Add entity to knowledge graph
    // (In real implementation, this would be done through the HTTP handler)
    info!("Added entity: {}", entity_request.id);

    info!("\nREST API simulation completed!");
    info!("In a real implementation, you would:");
    info!("- Use a proper HTTP framework (axum, warp, actix-web)");
    info!("- Add authentication and rate limiting");
    info!("- Implement proper error handling and validation");
    info!("- Add OpenAPI/Swagger documentation");
    info!("- Use connection pooling for concurrent requests");

    Ok(())
}