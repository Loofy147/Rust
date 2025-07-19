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

use proptest::prelude::*;

#[tokio::test]
async fn test_create_agent() {
    let config = AgentConfig::from_env().unwrap();
    let knowledge_graph = InMemoryKnowledgeGraph::new();
    let vector_store = InMemoryVectorStore::new();
    let metrics = MetricsCollector::new();
    let llm_plugin = Box::new(MockLLMPlugin::new());
    let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

    let agent = ReasoningAgent::new(
        knowledge_graph,
        vector_store,
        llm_plugin,
        prompt_builder,
        metrics,
        config.performance.max_concurrent_tasks,
        config.performance.task_timeout_seconds,
    )
    .unwrap();

    let result = agent.process_task("test task").await;
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), "Processed task: test task");
}

proptest! {
    #[test]
    fn test_process_task_proptest(task in "\\PC*") {
        tokio::runtime::Runtime::new().unwrap().block_on(async {
            let config = AgentConfig::from_env().unwrap();
            let knowledge_graph = InMemoryKnowledgeGraph::new();
            let vector_store = InMemoryVectorStore::new();
            let metrics = MetricsCollector::new();
            let llm_plugin = Box::new(MockLLMPlugin::new());
            let prompt_builder = Box::new(DefaultPromptBuilderPlugin::new());

            let agent = ReasoningAgent::new(
                knowledge_graph,
                vector_store,
                llm_plugin,
                prompt_builder,
                metrics,
                config.performance.max_concurrent_tasks,
                config.performance.task_timeout_seconds,
            )
            .unwrap();

            let result = agent.process_task(&task).await;
            assert!(result.is_ok());
            assert_eq!(result.unwrap(), format!("Processed task: {}", task));
        });
    }
}
