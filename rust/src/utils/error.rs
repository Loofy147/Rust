use thiserror::Error;

#[derive(Error, Debug)]
pub enum KnowledgeGraphError {
    #[error("Query failed: {0}")]
    Query(String),
}

#[derive(Error, Debug)]
pub enum VectorStoreError {
    #[error("Operation failed: {0}")]
    Operation(String),
}

#[derive(Error, Debug)]
pub enum AgentError {
    #[error("Knowledge graph query failed: {source}")]
    KnowledgeGraphError {
        #[from]
        source: KnowledgeGraphError,
    },

    #[error("LLM plugin error: {message}")]
    LlmPluginError { message: String },

    #[error("Vector store operation failed")]
    VectorStoreError(#[from] VectorStoreError),

    #[error("Timeout occurred after {duration_ms}ms")]
    TimeoutError { duration_ms: u64 },

    #[error("Rate limit exceeded: {requests_per_second} req/s")]
    RateLimitError { requests_per_second: u32 },

    #[error("Configuration error: {message}")]
    Config { message: String },

    #[error("IO error: {source}")]
    Io {
        #[from]
        source: std::io::Error,
    },
}

impl AgentError {
    pub fn with_context<T: std::fmt::Display>(self, context: T) -> anyhow::Error {
        anyhow::Error::from(self).context(context.to_string())
    }
}

pub type Result<T> = std::result::Result<T, AgentError>;
