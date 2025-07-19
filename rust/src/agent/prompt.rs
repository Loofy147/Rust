use crate::storage::memory::KnowledgeEntity;
use crate::storage::vector_store::VectorSimilarity;

pub struct PromptContext<'a> {
    pub task: &'a str,
    pub kg_entities: Vec<KnowledgeEntity>,
    pub similar_vectors: Vec<VectorSimilarity>,
}
