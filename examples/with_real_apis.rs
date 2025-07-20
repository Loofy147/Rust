// This example shows how to use real LLM APIs
// To run: cargo run --example with_real_apis --features llm-apis

#[cfg(feature = "llm-apis")]
use reasoning_agent::{
    ReasoningAgent,
    plugins::{OpenAILLMPlugin, HuggingFaceLLMPlugin, DefaultPromptBuilderPlugin},
    knowledge_graph::InMemoryKnowledgeGraph,
    vector_store::InMemoryVectorStore,
    metrics::MetricsCollector,
};

#[cfg(not(feature = "llm-apis"))]
use reasoning_agent::{
    ReasoningAgent,
    plugins::{MockLLMPlugin, DefaultPromptBuilderPlugin},
    knowledge_graph::InMemoryKnowledgeGraph,
    vector_store::InMemoryVectorStore,
    metrics::MetricsCollector,
};

use tracing::{info, Level};
use tracing_subscriber;
use std::env;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_max_level(Level::INFO)
        .init();

    info!("Running ReasoningAgent with LLM API integration");

    // Initialize components
    let knowledge_graph = InMemoryKnowledgeGraph::with_sample_data();
    let vector_store = InMemoryVectorStore::new();
    let metrics_collector = MetricsCollector::new();

    #[cfg(feature = "llm-apis")]
    let llm_plugin = {
        if let Ok(api_key) = env::var("OPENAI_API_KEY") {
            info!("Using OpenAI API");
            Box::new(OpenAILLMPlugin::new(api_key, Some("gpt-3.5-turbo".to_string())))
        } else if let Ok(hf_key) = env::var("HUGGINGFACE_API_KEY") {
            info!("Using Hugging Face API");
            Box::new(HuggingFaceLLMPlugin::new(
                hf_key,
                "microsoft/DialoGPT-medium".to_string()
            ))
        } else {
            info!("No API keys found, using mock LLM");
            Box::new(reasoning_agent::plugins::MockLLMPlugin::new()) 
                as Box<dyn reasoning_agent::plugins::LLMPlugin>
        }
    };

    #[cfg(not(feature = "llm-apis"))]
    let llm_plugin = {
        info!("LLM APIs feature not enabled, using mock LLM");
        Box::new(MockLLMPlugin::new())
    };

    let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

    // Create reasoning agent
    let mut agent = ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics_collector,
    );

    // Process task
    let task = "Explain the relationship between renewable energy adoption and economic benefits";
    info!("Processing task: {}", task);
    
    let result = agent.process_task(task).await?;
    info!("Task result: {}", result);

    // Print metrics
    agent.print_metrics();

    Ok(())
}