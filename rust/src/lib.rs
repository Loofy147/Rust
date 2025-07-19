//! Reasoning Agent Library
//!
//! A sophisticated reasoning agent that integrates knowledge graphs, vector similarity search,
//! and Large Language Models through a flexible plugin architecture.

pub mod agent;
pub mod plugins;
pub mod storage;
pub mod metrics;
pub mod utils;

#[cfg(feature = "api")]
pub mod api;

#[cfg(feature = "cli")]
pub mod cli;

// Re-export commonly used items
pub use agent::{ReasoningAgent, core::ReasoningAgent as Agent};
pub use plugins::traits::{LLMPlugin, PromptBuilderPlugin};
pub use storage::{InMemoryKnowledgeGraph, InMemoryVectorStore};
pub use metrics::MetricsCollector;
pub use utils::error::{Result, AgentError};

// Feature-gated re-exports
#[cfg(feature = "llm-apis")]
pub use plugins::llm::{OpenAILLMPlugin, HuggingFaceLLMPlugin};
