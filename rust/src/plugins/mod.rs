//! Plugin system for extensible functionality

pub mod traits;
pub mod llm;
pub mod prompt;
pub mod manager;

pub use traits::{LLMPlugin, PromptBuilderPlugin};
