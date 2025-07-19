use reasoning_agent::{
    ReasoningAgent,
    plugins::{MockLLMPlugin, DefaultPromptBuilderPlugin},
    knowledge_graph::InMemoryKnowledgeGraph,
    vector_store::InMemoryVectorStore,
    metrics::MetricsCollector,
};
use tracing::{info, Level};
use tracing_subscriber;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();

    info!("Starting ReasoningAgent system");

    // Initialize components with sample data
    let knowledge_graph = InMemoryKnowledgeGraph::with_sample_data();
    let vector_store = InMemoryVectorStore::new();
    let metrics_collector = MetricsCollector::new();
    
    // Initialize plugins - use mock LLM for now, can be swapped for real APIs
    let llm_plugin = Box::new(MockLLMPlugin::new());
    let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

    // Create reasoning agent
    let mut agent = ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics_collector,
    );

    // Example task processing
    let task = "What are the potential benefits of renewable energy?";
    info!("Processing task: {}", task);
    
    let result = agent.process_task(task).await?;
    info!("Task result: {}", result);

    // Print metrics
    agent.print_metrics();

    Ok(())
}