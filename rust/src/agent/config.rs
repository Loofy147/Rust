use secrecy::Secret;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct PerformanceConfig {
    pub max_concurrent_tasks: usize,
    pub task_timeout_seconds: u64,
    pub cache_size: usize,
    pub batch_size: usize,
}

#[derive(Debug, Deserialize)]
pub struct AgentConfig {
    pub llm_api_key: Option<Secret<String>>,
    pub performance: PerformanceConfig,
}

impl AgentConfig {
    pub fn from_env() -> Result<Self, config::ConfigError> {
        let config = config::Config::builder()
            .add_source(config::File::with_name("config/default").required(false))
            .add_source(config::Environment::with_prefix("AGENT"))
            .build()?;
        config.try_deserialize()
    }
}
