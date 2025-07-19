//! Plugin system for extensible functionality

pub mod traits;
pub mod llm;
pub mod prompt;

pub use traits::{LLMPlugin, PromptBuilderPlugin};
