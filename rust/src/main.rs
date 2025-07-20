//! Reasoning Agent CLI Application

use clap::Parser;
use reasoning_agent::{
    agent::AgentConfig,
    metrics::MetricsCollector,
    plugins::{
        prompt::default::DefaultPromptBuilderPlugin,
        traits::MockLLMPlugin,
    },
    storage::{InMemoryKnowledgeGraph, InMemoryVectorStore},
    ReasoningAgent,
};

use reasoning_agent::cli::commands::{Cli, Commands};

use tracing_subscriber::{fmt, EnvFilter};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));
    fmt().with_env_filter(filter).init();

    let cli = Cli::parse();

    match cli.command {
        Commands::Serve { host, port } => {
            println!("Starting reasoning agent server on {}:{}", host, port);
            // TODO: Implement server
            Ok(())
        }
        Commands::Process { task } => {
            let agent = create_agent().await?;
            let result = agent.process_task(&task).await?;
            println!("Result: {}", result);
            Ok(())
        }
        Commands::Info => {
            println!("Reasoning Agent v{}", env!("CARGO_PKG_VERSION"));
            println!("Built with Rust {}", std::env::var("RUSTC_VERSION").unwrap_or_else(|_| "unknown".to_string()));
            Ok(())
        }
    }
}

async fn create_agent() -> anyhow::Result<ReasoningAgent> {
    let config = AgentConfig::from_env()?;
    let knowledge_graph = InMemoryKnowledgeGraph::new();
    let vector_store = InMemoryVectorStore::new();
    let metrics = MetricsCollector::new();
    let llm_plugin = Box::new(MockLLMPlugin::new());
    let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

    Ok(ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics,
        config.performance.max_concurrent_tasks,
        config.performance.task_timeout_seconds,
    )?)
}
