use async_trait::async_trait;
use reqwest;
use serde_json;
use std::collections::HashMap;
use crate::plugins::traits::{LLMPlugin, PluginError};
use crate::plugins::llm::mock::{LLMRequest, LLMResponse};

/// Hugging Face plugin for open source models
#[cfg(feature = "llm-apis")]
pub struct HuggingFaceLLMPlugin {
    api_key: String,
    model: String,
    client: reqwest::Client,
}

#[cfg(feature = "llm-apis")]
impl HuggingFaceLLMPlugin {
    pub fn new(api_key: String, model: String) -> Self {
        Self {
            api_key,
            model,
            client: reqwest::Client::new(),
        }
    }
}

#[cfg(feature = "llm-apis")]
#[async_trait]
impl LLMPlugin for HuggingFaceLLMPlugin {
    async fn generate(&self, request: &LLMRequest) -> Result<LLMResponse, PluginError> {
        let mut payload = HashMap::new();
        payload.insert("inputs", request.prompt.clone());

        let mut parameters = HashMap::new();
        if let Some(max_tokens) = request.max_tokens {
            parameters.insert("max_new_tokens", max_tokens);
        }
        if let Some(temperature) = request.temperature {
            parameters.insert("temperature", temperature as u32);
        }
        payload.insert("parameters", serde_json::to_string(&parameters)?);

        let url = format!("https://api-inference.huggingface.co/models/{}", self.model);

        let response = self
            .client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(PluginError::Api(format!(
                "Hugging Face API returned status: {}",
                response.status()
            )));
        }

        let response_data: serde_json::Value = response.json().await?;

        let content = if response_data.is_array() {
            response_data[0]["generated_text"]
                .as_str()
                .unwrap_or("No response generated")
                .to_string()
        } else {
            response_data["generated_text"]
                .as_str()
                .unwrap_or("No response generated")
                .to_string()
        };

        Ok(LLMResponse {
            content,
            tokens_used: None, // HF doesn't always provide token counts
            model: self.model.clone(),
        })
    }

    fn get_model_name(&self) -> String {
        self.model.clone()
    }
}
