use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::env;

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

#[pyfunction]
fn call_openai(prompt: String, model: Option<String>, max_tokens: Option<u32>, temperature: Option<f32>) -> PyResult<String> {
    let api_key = env::var("OPENAI_API_KEY").map_err(|_| pyo3::exceptions::PyValueError::new_err("OPENAI_API_KEY not set"))?;
    let model = model.unwrap_or_else(|| "text-davinci-003".to_string());
    let max_tokens = max_tokens.unwrap_or(256);
    let temperature = temperature.unwrap_or(0.7);
    let client = reqwest::blocking::Client::new();
    let req_body = OpenAIRequest {
        model: model.clone(),
        prompt: prompt.clone(),
        max_tokens,
        temperature,
    };
    let resp = client
        .post("https://api.openai.com/v1/completions")
        .bearer_auth(api_key)
        .json(&req_body)
        .send()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Request error: {}", e)))?;
    let resp_json: OpenAIResponse = resp.json().map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Response parse error: {}", e)))?;
    let answer = resp_json.choices.get(0).map(|c| c.text.clone()).unwrap_or_default();
    Ok(answer)
}

#[pymodule]
fn reasoning_agent(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_openai, m)?)?;
    Ok(())
}
