pub mod plugins;
pub mod knowledge_graph;
pub mod vector_store;
pub mod metrics;
pub mod types;

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::time::Instant;
use tracing::{info, warn};
use uuid::Uuid;

use crate::{
    knowledge_graph::KnowledgeGraph,
    vector_store::VectorStore,
    plugins::{LLMPlugin, PromptBuilderPlugin},
    metrics::MetricsCollector,
    types::*,
};

/// Main ReasoningAgent that orchestrates task processing through KG queries,
/// vector similarity, prompt building, LLM calls, and metrics collection
pub struct ReasoningAgent<KG, VS, LLM, PB> 
where
    KG: KnowledgeGraph,
    VS: VectorStore,
    LLM: LLMPlugin,
    PB: PromptBuilderPlugin,
{
    knowledge_graph: KG,
    vector_store: VS,
    llm_plugin: Box<LLM>,
    prompt_builder: Box<PB>,
    metrics: MetricsCollector,
}

impl<KG, VS, LLM, PB> ReasoningAgent<KG, VS, LLM, PB>
where
    KG: KnowledgeGraph,
    VS: VectorStore,
    LLM: LLMPlugin,
    PB: PromptBuilderPlugin,
{
    pub fn new(
        knowledge_graph: KG,
        vector_store: VS,
        llm_plugin: Box<LLM>,
        prompt_builder: Box<PB>,
        metrics: MetricsCollector,
    ) -> Self {
        Self {
            knowledge_graph,
            vector_store,
            llm_plugin,
            prompt_builder,
            metrics,
        }
    }

    /// Main task processing pipeline: task → reasoning → metrics
    pub async fn process_task(&mut self, task: &str) -> anyhow::Result<String> {
        let start_time = Instant::now();
        let task_id = Uuid::new_v4();
        
        info!("Starting task processing: {}", task_id);
        self.metrics.record_task_started();

        // Step 1: Query KG for context
        let kg_context = self.query_knowledge_graph(task).await?;
        info!("Retrieved {} KG entities", kg_context.len());

        // Step 2: Query vector store for similar content
        let similar_content = self.query_vector_similarities(task).await?;
        info!("Found {} similar vectors", similar_content.len());

        // Step 3: Build prompt using context
        let prompt = self.build_prompt(task, &kg_context, &similar_content).await?;
        info!("Built prompt with {} characters", prompt.len());

        // Step 4: Call LLM
        let response = self.call_llm(&prompt).await?;
        info!("Received LLM response with {} characters", response.len());

        // Step 5: Store answer back into KG
        self.store_answer_to_kg(task, &response, task_id).await?;

        // Step 6: Emit metrics
        let duration = start_time.elapsed();
        self.metrics.record_task_completed(duration);
        info!("Task completed in {:?}", duration);

        Ok(response)
    }

    async fn query_knowledge_graph(&self, query: &str) -> anyhow::Result<Vec<KnowledgeEntity>> {
        self.metrics.record_kg_query();
        self.knowledge_graph.query_entities(query).await
    }

    async fn query_vector_similarities(&self, query: &str) -> anyhow::Result<Vec<VectorSimilarity>> {
        self.metrics.record_vector_search();
        self.vector_store.find_similar(query, 5).await
    }

    async fn build_prompt(
        &self,
        task: &str,
        kg_context: &[KnowledgeEntity],
        similar_content: &[VectorSimilarity],
    ) -> anyhow::Result<String> {
        let context = PromptContext {
            task: task.to_string(),
            kg_entities: kg_context.to_vec(),
            similar_vectors: similar_content.to_vec(),
        };
        self.prompt_builder.build_prompt(&context).await
    }

    async fn call_llm(&mut self, prompt: &str) -> anyhow::Result<String> {
        let request = LLMRequest {
            prompt: prompt.to_string(),
            max_tokens: Some(500),
            temperature: Some(0.7),
        };
        
        let llm_start = Instant::now();
        match self.llm_plugin.generate(&request).await {
            Ok(response) => {
                let llm_duration = llm_start.elapsed();
                self.metrics.record_llm_success();
                self.metrics.record_llm_response_time(llm_duration);
                Ok(response.content)
            }
            Err(e) => {
                self.metrics.record_llm_error();
                warn!("LLM call failed: {}", e);
                Err(e.into())
            }
        }
    }

    async fn store_answer_to_kg(
        &mut self,
        task: &str,
        answer: &str,
        task_id: Uuid,
    ) -> anyhow::Result<()> {
        let entity = KnowledgeEntity {
            id: task_id.to_string(),
            entity_type: "reasoning_result".to_string(),
            properties: vec![
                ("task".to_string(), task.to_string()),
                ("answer".to_string(), answer.to_string()),
                ("timestamp".to_string(), chrono::Utc::now().to_rfc3339()),
            ],
        };

        self.knowledge_graph.add_entity(entity).await?;
        
        // Also store in vector store for future similarity searches
        self.vector_store.add_document(&format!("{}: {}", task, answer)).await?;
        
        Ok(())
    }

    pub fn print_metrics(&self) {
        self.metrics.print_summary();
    }

    pub fn get_metrics(&self) -> &MetricsCollector {
        &self.metrics
    }
}