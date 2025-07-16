use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::{env, thread, time::Duration};
use log::{info, error, warn};

#[derive(Serialize, Deserialize)]
struct OpenAIRequest {
    model: String,
    prompt: String,
    max_tokens: u32,
    temperature: f32,
}

#[derive(Serialize, Deserialize)]
struct OpenAIResponse {
    choices: Vec<Choice>,
}

#[derive(Serialize, Deserialize)]
struct Choice {
    text: String,
}

fn setup_logger() {
    static INIT: std::sync::Once = std::sync::Once::new();
    INIT.call_once(|| {
        env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    });
}

fn get_env_or_default(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}

#[pyfunction]
pub fn call_openai(prompt: String, model: Option<String>, max_tokens: Option<u32>, temperature: Option<f32>) -> PyResult<String> {
    setup_logger();
    let api_key = env::var("OPENAI_API_KEY").map_err(|_| pyo3::exceptions::PyValueError::new_err("OPENAI_API_KEY not set"))?;
    let model = model.unwrap_or_else(|| get_env_or_default("OPENAI_MODEL", "text-davinci-003"));
    let max_tokens = max_tokens.unwrap_or_else(|| get_env_or_default("OPENAI_MAX_TOKENS", "256").parse().unwrap_or(256));
    let temperature = temperature.unwrap_or_else(|| get_env_or_default("OPENAI_TEMPERATURE", "0.7").parse().unwrap_or(0.7));
    let req = OpenAIRequest { model: model.clone(), prompt: prompt.clone(), max_tokens, temperature };
    let client = reqwest::blocking::Client::new();
    let url = "https://api.openai.com/v1/completions";
    let mut retries = get_env_or_default("OPENAI_RETRIES", "3").parse().unwrap_or(3);
    let mut backoff = 1;
    loop {
        info!("Calling OpenAI: model={}, max_tokens={}, temp={}, prompt_len={}", model, max_tokens, temperature, prompt.len());
        let resp = client.post(url)
            .bearer_auth(&api_key)
            .json(&req)
            .send();
        match resp {
            Ok(r) => {
                if r.status().is_success() {
                    let json: OpenAIResponse = r.json().map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("OpenAI JSON error: {}", e)))?;
                    if let Some(choice) = json.choices.get(0) {
                        info!("OpenAI call succeeded");
                        return Ok(choice.text.clone());
                    } else {
                        error!("OpenAI response missing choices");
                        return Err(pyo3::exceptions::PyValueError::new_err("No choices in OpenAI response"));
                    }
                } else {
                    warn!("OpenAI HTTP error: {}", r.status());
                    if retries > 0 && r.status().is_server_error() {
                        retries -= 1;
                        thread::sleep(Duration::from_secs(backoff));
                        backoff *= 2;
                        continue;
                    }
                    return Err(pyo3::exceptions::PyValueError::new_err(format!("OpenAI HTTP error: {}", r.status())));
                }
            }
            Err(e) => {
                error!("OpenAI network error: {}", e);
                if retries > 0 {
                    retries -= 1;
                    thread::sleep(Duration::from_secs(backoff));
                    backoff *= 2;
                    continue;
                }
                return Err(pyo3::exceptions::PyValueError::new_err(format!("OpenAI network error: {}", e)));
            }
        }
    }
}

#[pymodule]
fn reasoning_agent(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_openai, m)?)?;
    Ok(())
}
