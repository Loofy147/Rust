use async_trait::async_trait;
use crate::agent::prompt::PromptContext;
use crate::plugins::traits::PromptBuilderPlugin;

/// Enhanced prompt builder with more sophisticated prompt engineering
pub struct EnhancedPromptBuilderPlugin;

impl EnhancedPromptBuilderPlugin {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl PromptBuilderPlugin for EnhancedPromptBuilderPlugin {
    async fn build_prompt(&self, context: &PromptContext) -> anyhow::Result<String> {
        let mut prompt = String::new();

        // Enhanced system instruction with reasoning guidance
        prompt.push_str(r#"You are an expert AI reasoning assistant with access to a knowledge graph and vector database.

Instructions:
1. Analyze the task carefully
2. Use the provided knowledge graph entities as factual grounding
3. Consider the similar content for additional context and patterns
4. Reason step-by-step through the problem
5. Provide a well-structured, evidence-based response
6. Cite specific entities or similar content when relevant

"#);

        // Task with emphasis
        prompt.push_str(&format!("## Task\n{}\n\n", context.task));

        // Structured knowledge context
        if !context.kg_entities.is_empty() {
            prompt.push_str("## Knowledge Graph Entities\n");
            for (i, entity) in context.kg_entities.iter().enumerate() {
                prompt.push_str(&format!("### Entity {} - {} ({})\n", i+1, entity.entity_type, entity.id));
                for (key, value) in &entity.properties {
                    prompt.push_str(&format!("- **{}**: {}\n", key, value));
                }
                prompt.push('\n');
            }
        }

        // Structured similar content
        if !context.similar_vectors.is_empty() {
            prompt.push_str("## Similar Content (Ranked by Relevance)\n");
            for (i, similarity) in context.similar_vectors.iter().enumerate() {
                prompt.push_str(&format!(
                    "### Content {} (Similarity: {:.3})\n{}\n\n",
                    i+1,
                    similarity.similarity_score,
                    similarity.content
                ));
            }
        }

        prompt.push_str("## Response\nProvide your analysis and answer:");

        Ok(prompt)
    }
}
