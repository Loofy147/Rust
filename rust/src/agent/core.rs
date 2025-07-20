use serde::{Deserialize, Serialize};
use crate::storage::memory::KnowledgeGraph;
use crate::storage::vector_store::VectorStore;
use crate::plugins::traits::{LLMPlugin, PromptBuilderPlugin};
use crate::metrics::collector::MetricsCollector;
use crate::utils::error::AgentError;
use anyhow::Result;
use std::sync::Arc;
use tokio::sync::Semaphore;
use tokio::time::{timeout, Duration};
use tracing::{info, instrument, Span};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReasoningAgent {
    pub id: String,
    #[serde(skip, default = "default_semaphore")]
    semaphore: Arc<Semaphore>,
    task_timeout_seconds: u64,
}

fn default_semaphore() -> Arc<Semaphore> {
    Arc::new(Semaphore::new(10))
}

impl ReasoningAgent {
    pub fn new(
        _knowledge_graph: impl KnowledgeGraph + 'static,
        _vector_store: impl VectorStore + 'static,
        _llm_plugin: Box<dyn LLMPlugin>,
        _prompt_builder: Box<dyn PromptBuilderPlugin>,
        _metrics: MetricsCollector,
        max_concurrent_tasks: usize,
        task_timeout_seconds: u64,
    ) -> Result<Self> {
        Ok(Self {
            id: "agent-1".to_string(),
            semaphore: Arc::new(Semaphore::new(max_concurrent_tasks)),
            task_timeout_seconds,
        })
    }

    #[instrument(skip(self), fields(task_id = %uuid::Uuid::new_v4()))]
    pub async fn process_task(&self, task: &str) -> Result<String> {
        let _permit = self.semaphore.acquire().await?;
        let span = Span::current();
        span.record("task_length", &task.len());

        info!("Starting task processing");

        let duration = Duration::from_secs(self.task_timeout_seconds);
        timeout(duration, async {
            // ... existing implementation ...
            Ok(format!("Processed task: {}", task))
        })
        .await
        .map_err(|_| AgentError::TimeoutError {
            duration_ms: duration.as_millis() as u64,
        })?
    }
}
