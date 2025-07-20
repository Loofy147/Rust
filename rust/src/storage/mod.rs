//! Storage backends for knowledge graphs and vector stores

pub mod memory;
pub mod vector_store;

#[cfg(feature = "database")]
pub mod persistent;

pub use memory::InMemoryKnowledgeGraph;
pub use vector_store::{VectorStore, InMemoryVectorStore};

#[cfg(feature = "database")]
pub use persistent::{SQLiteKnowledgeGraph, SQLiteVectorStore};
