use reasoning_agent::{
    ReasoningAgent,
    plugins::{MockLLMPlugin, EnhancedPromptBuilderPlugin},
    knowledge_graph::{InMemoryKnowledgeGraph, KnowledgeGraph},
    vector_store::{InMemoryVectorStore, VectorStore},
    metrics::MetricsCollector,
    types::KnowledgeEntity,
};
use tracing::{info, Level};
use tracing_subscriber;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();

    info!("Running basic ReasoningAgent usage example");

    // Initialize components with sample data
    let mut knowledge_graph = InMemoryKnowledgeGraph::with_sample_data();
    let mut vector_store = InMemoryVectorStore::new();
    let metrics_collector = MetricsCollector::new();

    // Add custom knowledge to demonstrate KG integration
    let custom_entity = KnowledgeEntity {
        id: "energy_storage_001".to_string(),
        entity_type: "technology".to_string(),
        properties: vec![
            ("name".to_string(), "Battery Energy Storage".to_string()),
            ("benefit".to_string(), "Enables grid stability and renewable integration".to_string()),
            ("cost_trend".to_string(), "Decreasing rapidly due to lithium-ion advances".to_string()),
        ],
    };
    knowledge_graph.add_entity(custom_entity).await?;

    // Add custom content to vector store
    vector_store.add_document("Energy storage systems are crucial for the renewable energy transition, allowing excess power to be stored and used when generation is low.").await?;

    // Initialize plugins with enhanced prompt building
    let llm_plugin = Box::new(MockLLMPlugin::new());
    let prompt_builder = Box::new(EnhancedPromptBuilderPlugin::new());

    // Create reasoning agent
    let mut agent = ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics_collector,
    );

    // Example 1: Energy-related query that should match our KG data
    info!("\n=== Example 1: Energy Query ===");
    let result1 = agent.process_task("What are the main advantages of renewable energy storage?").await?;
    info!("Result 1: {}", result1);

    // Example 2: Technology query
    info!("\n=== Example 2: Technology Query ===");
    let result2 = agent.process_task("How does solar power technology compare to other renewable sources?").await?;
    info!("Result 2: {}", result2);

    // Example 3: Climate-related query
    info!("\n=== Example 3: Climate Query ===");
    let result3 = agent.process_task("What role does renewable energy play in addressing climate change?").await?;
    info!("Result 3: {}", result3);

    // Print comprehensive metrics
    info!("\n=== Final Metrics ===");
    agent.print_metrics();

    // Export metrics as JSON
    if let Ok(metrics_json) = agent.get_metrics().export_metrics_json() {
        info!("Metrics JSON: {}", metrics_json);
    }

    Ok(())
}