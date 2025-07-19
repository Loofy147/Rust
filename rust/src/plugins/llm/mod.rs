//! LLM plugin implementations

pub mod mock;

#[cfg(feature = "llm-apis")]
pub mod openai;

#[cfg(feature = "llm-apis")]
pub mod huggingface;


#[cfg(feature = "llm-apis")]
pub use openai::OpenAILLMPlugin;

#[cfg(feature = "llm-apis")]
pub use huggingface::HuggingFaceLLMPlugin;
