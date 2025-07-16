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

fn get_env_or_default<T: std::str::FromStr>(key: &str, default: T) -> T {
    env::var(key).ok().and_then(|v| v.parse().ok()).unwrap_or(default)
}

#[pyfunction]
fn call_openai(prompt: String, model: Option<String>, max_tokens: Option<u32>, temperature: Option<f32>) -> PyResult<String> {
    setup_logger();
    let api_key = env::var("OPENAI_API_KEY").map_err(|_| pyo3::exceptions::PyValueError::new_err("OPENAI_API_KEY not set"))?;
    let model = model.or_else(|| env::var("OPENAI_MODEL").ok()).unwrap_or_else(|| "text-davinci-003".to_string());
    let max_tokens = max_tokens.or_else(|| env::var("OPENAI_MAX_TOKENS").ok().and_then(|v| v.parse().ok())).unwrap_or(256);
    let temperature = temperature.or_else(|| env::var("OPENAI_TEMPERATURE").ok().and_then(|v| v.parse().ok())).unwrap_or(0.7);
    let client = reqwest::blocking::Client::new();
    let req_body = OpenAIRequest {
        model: model.clone(),
        prompt: prompt.clone(),
        max_tokens,
        temperature,
    };
    let max_retries = get_env_or_default("OPENAI_MAX_RETRIES", 3);
    let mut attempt = 0;
    let mut last_err = None;
    while attempt < max_retries {
        attempt += 1;
        info!("[OpenAI] Attempt {}: model={}, max_tokens={}, temperature={}", attempt, model, max_tokens, temperature);
        match client
            .post("https://api.openai.com/v1/completions")
            .bearer_auth(&api_key)
            .json(&req_body)
            .send()
        {
            Ok(resp) => {
                let status = resp.status();
                if !status.is_success() {
                    warn!("[OpenAI] Non-success status: {}", status);
                    last_err = Some(format!("OpenAI API error: status {}", status));
                    if status.is_server_error() || status.as_u16() == 429 {
                        thread::sleep(Duration::from_millis(500 * attempt));
                        continue;
                    } else {
                        break;
                    }
                }
                match resp.json::<OpenAIResponse>() {
                    Ok(resp_json) => {
                        let answer = resp_json.choices.get(0).map(|c| c.text.clone()).unwrap_or_default();
                        info!("[OpenAI] Success: {} chars", answer.len());
                        return Ok(answer);
                    }
                    Err(e) => {
                        error!("[OpenAI] Response parse error: {}", e);
                        last_err = Some(format!("Response parse error: {}", e));
                        break;
                    }
                }
            }
            Err(e) => {
                warn!("[OpenAI] Request error: {}", e);
                last_err = Some(format!("Request error: {}", e));
                thread::sleep(Duration::from_millis(500 * attempt));
            }
        }
    }
    Err(pyo3::exceptions::PyRuntimeError::new_err(last_err.unwrap_or_else(|| "Unknown error".to_string())))
}

#[pymodule]
fn reasoning_agent(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_openai, m)?)?;
    Ok(())
}
