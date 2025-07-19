use thiserror::Error;

#[derive(Error, Debug)]
pub enum AgentError {
    #[error("Configuration error: {message}")]
    Config { message: String },

    #[error("Plugin error: {0}")]
    Plugin(String),

    #[error("Storage error: {message}")]
    Storage { message: String },

    #[error("Processing error: {message}")]
    Processing { message: String },

    #[error("IO error: {source}")]
    Io {
        #[from]
        source: std::io::Error,
    },
}

pub type Result<T> = std::result::Result<T, AgentError>;
