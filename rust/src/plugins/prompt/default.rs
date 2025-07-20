use async_trait::async_trait;
use crate::agent::prompt::PromptContext;
use crate::plugins::traits::PromptBuilderPlugin;

/// Default prompt builder that creates structured prompts from context
pub struct DefaultPromptBuilderPlugin;

impl DefaultPromptBuilderPlugin {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait]
impl PromptBuilderPlugin for DefaultPromptBuilderPlugin {
    async fn build_prompt(&self, context: &PromptContext) -> anyhow::Result<String> {
        let mut prompt = String::new();

        // System instruction
        prompt.push_str("You are an AI reasoning assistant. Use the provided context to answer the user's task.\n\n");

        // Task
        prompt.push_str(&format!("Task: {}\n\n", context.task));

        // Knowledge Graph context
        if !context.kg_entities.is_empty() {
            prompt.push_str("Knowledge Graph Context:\n");
            for entity in &context.kg_entities {
                prompt.push_str(&format!("- {} ({}): ", entity.entity_type, entity.id));
                for (key, value) in &entity.properties {
                    prompt.push_str(&format!("{}={}, ", key, value));
                }
                prompt.push('\n');
            }
            prompt.push('\n');
        }

        // Similar content
        if !context.similar_vectors.is_empty() {
            prompt.push_str("Similar Content:\n");
            for similarity in &context.similar_vectors {
                prompt.push_str(&format!(
                    "- (similarity: {:.3}) {}\n",
                    similarity.similarity_score,
                    similarity.content.chars().take(200).collect::<String>()
                ));
            }
            prompt.push('\n');
        }

        prompt.push_str("Please provide a comprehensive answer based on the above context:");

        Ok(prompt)
    }
}
