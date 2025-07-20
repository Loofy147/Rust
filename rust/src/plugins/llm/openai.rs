use async_trait::async_trait;
use reqwest;
use serde_json;
use std::collections::HashMap;
use crate::plugins::traits::{LLMPlugin, PluginError};
use crate::plugins::llm::mock::{LLMRequest, LLMResponse};

/// OpenAI GPT plugin for real LLM interactions
#[cfg(feature = "llm-apis")]
pub struct OpenAILLMPlugin {
    api_key: String,
    model: String,
    client: reqwest::Client,
}

#[cfg(feature = "llm-apis")]
impl OpenAILLMPlugin {
    pub fn new(api_key: String, model: Option<String>) -> Self {
        Self {
            api_key,
            model: model.unwrap_or_else(|| "gpt-3.5-turbo".to_string()),
            client: reqwest::Client::new(),
        }
    }
}

#[cfg(feature = "llm-apis")]
#[async_trait]
impl LLMPlugin for OpenAILLMPlugin {
    async fn generate(&self, request: &LLMRequest) -> Result<LLMResponse, PluginError> {
        let mut payload = HashMap::new();
        payload.insert("model", self.model.clone());
        payload.insert("prompt", request.prompt.clone());

        if let Some(max_tokens) = request.max_tokens {
            payload.insert("max_tokens", max_tokens.to_string());
        }
        if let Some(temperature) = request.temperature {
            payload.insert("temperature", temperature.to_string());
        }

        let response = self
            .client
            .post("https://api.openai.com/v1/completions")
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(PluginError::Api(format!(
                "OpenAI API returned status: {}",
                response.status()
            )));
        }

        let response_data: serde_json::Value = response.json().await?;

        let content = response_data["choices"][0]["text"]
            .as_str()
            .ok_or_else(|| PluginError::Api("Invalid response format".to_string()))?
            .trim()
            .to_string();

        let tokens_used = response_data["usage"]["total_tokens"]
            .as_u64()
            .map(|t| t as u32);

        Ok(LLMResponse {
            content,
            tokens_used,
            model: self.model.clone(),
        })
    }

    fn get_model_name(&self) -> String {
        self.model.clone()
    }
}
