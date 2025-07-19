use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct AgentConfig {
    pub llm_api_key: Option<String>,
}

impl AgentConfig {
    pub fn from_env() -> Result<Self, config::ConfigError> {
        let config = config::Config::builder()
            .add_source(config::Environment::with_prefix("AGENT"))
            .build()?;
        config.try_deserialize()
    }
}
