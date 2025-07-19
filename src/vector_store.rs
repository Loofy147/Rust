use async_trait::async_trait;
use dashmap::DashMap;
use std::sync::Arc;
use uuid::Uuid;
use std::collections::HashMap;

use crate::types::VectorSimilarity;

/// Trait for vector store operations
#[async_trait]
pub trait VectorStore: Send + Sync {
    async fn add_document(&mut self, content: &str) -> anyhow::Result<String>;
    async fn add_vector(&mut self, id: &str, vector: Vec<f32>, content: &str) -> anyhow::Result<()>;
    async fn find_similar(&self, query: &str, limit: usize) -> anyhow::Result<Vec<VectorSimilarity>>;
    async fn find_similar_by_vector(&self, query_vector: &[f32], limit: usize) -> anyhow::Result<Vec<VectorSimilarity>>;
    async fn remove_document(&mut self, id: &str) -> anyhow::Result<bool>;
    async fn get_document_count(&self) -> usize;
}

#[derive(Clone)]
struct DocumentVector {
    id: String,
    content: String,
    vector: Vec<f32>,
}

/// In-memory vector store implementation with simple similarity computation
pub struct InMemoryVectorStore {
    documents: Arc<DashMap<String, DocumentVector>>,
    dimension: usize,
}

impl InMemoryVectorStore {
    pub fn new() -> Self {
        Self::with_dimension(384) // Default embedding dimension
    }

    pub fn with_dimension(dimension: usize) -> Self {
        let store = Self {
            documents: Arc::new(DashMap::new()),
            dimension,
        };
        
        // Add some sample vectors for demonstration
        store.add_sample_data();
        store
    }

    fn add_sample_data(&self) {
        let sample_docs = vec![
            ("Solar energy is a renewable source of power that harnesses sunlight to generate electricity.", vec![0.8, 0.2, 0.9, 0.1]),
            ("Wind turbines convert wind energy into electrical power through rotating blades.", vec![0.7, 0.3, 0.8, 0.2]),
            ("Hydroelectric power uses flowing water to generate clean electricity.", vec![0.6, 0.4, 0.7, 0.3]),
            ("Fossil fuels like coal and oil are non-renewable energy sources.", vec![0.2, 0.8, 0.1, 0.9]),
            ("Climate change is caused by greenhouse gas emissions from human activities.", vec![0.3, 0.7, 0.2, 0.8]),
        ];

        for (content, partial_vector) in sample_docs {
            let id = Uuid::new_v4().to_string();
            // Extend partial vector to full dimension
            let mut vector = partial_vector;
            while vector.len() < self.dimension {
                vector.push(0.5); // Fill with neutral values
            }
            vector.truncate(self.dimension);

            let doc = DocumentVector {
                id: id.clone(),
                content: content.to_string(),
                vector,
            };
            self.documents.insert(id, doc);
        }
    }

    /// Simple text-to-vector conversion (in production, use proper embeddings)
    fn text_to_vector(&self, text: &str) -> Vec<f32> {
        let mut vector = vec![0.0; self.dimension];
        let lower_text = text.to_lowercase();
        let words: Vec<&str> = lower_text.split_whitespace().collect();
        
        // Simple bag-of-words approach with basic hashing
        for (i, word) in words.iter().enumerate() {
            let hash = self.simple_hash(word) % self.dimension;
            vector[hash] += 1.0 / (i + 1) as f32; // Weighted by position
        }
        
        // Normalize vector
        let magnitude: f32 = vector.iter().map(|x| x * x).sum::<f32>().sqrt();
        if magnitude > 0.0 {
            for val in &mut vector {
                *val /= magnitude;
            }
        }
        
        vector
    }

    fn simple_hash(&self, s: &str) -> usize {
        s.chars().fold(0, |acc, c| acc.wrapping_mul(31).wrapping_add(c as usize))
    }

    fn cosine_similarity(&self, a: &[f32], b: &[f32]) -> f32 {
        if a.len() != b.len() {
            return 0.0;
        }

        let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
        let magnitude_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
        let magnitude_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

        if magnitude_a == 0.0 || magnitude_b == 0.0 {
            0.0
        } else {
            dot_product / (magnitude_a * magnitude_b)
        }
    }
}

#[async_trait]
impl VectorStore for InMemoryVectorStore {
    async fn add_document(&mut self, content: &str) -> anyhow::Result<String> {
        let id = Uuid::new_v4().to_string();
        let vector = self.text_to_vector(content);
        self.add_vector(&id, vector, content).await?;
        Ok(id)
    }

    async fn add_vector(&mut self, id: &str, vector: Vec<f32>, content: &str) -> anyhow::Result<()> {
        if vector.len() != self.dimension {
            return Err(anyhow::anyhow!(
                "Vector dimension {} does not match expected dimension {}",
                vector.len(),
                self.dimension
            ));
        }

        let doc = DocumentVector {
            id: id.to_string(),
            content: content.to_string(),
            vector,
        };

        self.documents.insert(id.to_string(), doc);
        Ok(())
    }

    async fn find_similar(&self, query: &str, limit: usize) -> anyhow::Result<Vec<VectorSimilarity>> {
        let query_vector = self.text_to_vector(query);
        self.find_similar_by_vector(&query_vector, limit).await
    }

    async fn find_similar_by_vector(&self, query_vector: &[f32], limit: usize) -> anyhow::Result<Vec<VectorSimilarity>> {
        let mut similarities: Vec<VectorSimilarity> = Vec::new();

        for doc in self.documents.iter() {
            let similarity = self.cosine_similarity(query_vector, &doc.vector);
            similarities.push(VectorSimilarity {
                id: doc.id.clone(),
                content: doc.content.clone(),
                similarity_score: similarity,
            });
        }

        // Sort by similarity score (highest first)
        similarities.sort_by(|a, b| b.similarity_score.partial_cmp(&a.similarity_score).unwrap());
        similarities.truncate(limit);

        Ok(similarities)
    }

    async fn remove_document(&mut self, id: &str) -> anyhow::Result<bool> {
        Ok(self.documents.remove(id).is_some())
    }

    async fn get_document_count(&self) -> usize {
        self.documents.len()
    }
}

/// SQLite-based persistent vector store
#[cfg(feature = "sqlite")]
pub struct SQLiteVectorStore {
    pool: sqlx::SqlitePool,
    dimension: usize,
}

#[cfg(feature = "sqlite")]
impl SQLiteVectorStore {
    pub async fn new(database_url: &str, dimension: usize) -> anyhow::Result<Self> {
        let pool = sqlx::SqlitePool::connect(database_url).await?;
        
        // Create table if it doesn't exist
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                vector BLOB NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        "#)
        .execute(&pool)
        .await?;

        // Create index for faster similarity searches (if supported)
        let _ = sqlx::query(r#"
            CREATE INDEX IF NOT EXISTS idx_vectors_content ON vectors(content)
        "#)
        .execute(&pool)
        .await;

        Ok(Self { pool, dimension })
    }

    fn vector_to_bytes(&self, vector: &[f32]) -> Vec<u8> {
        vector.iter().flat_map(|&f| f.to_le_bytes().to_vec()).collect()
    }

    fn bytes_to_vector(&self, bytes: &[u8]) -> Vec<f32> {
        bytes
            .chunks_exact(4)
            .map(|chunk| f32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]))
            .collect()
    }

    fn cosine_similarity(&self, a: &[f32], b: &[f32]) -> f32 {
        if a.len() != b.len() {
            return 0.0;
        }

        let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
        let magnitude_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
        let magnitude_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

        if magnitude_a == 0.0 || magnitude_b == 0.0 {
            0.0
        } else {
            dot_product / (magnitude_a * magnitude_b)
        }
    }

    fn text_to_vector(&self, text: &str) -> Vec<f32> {
        // Simple implementation - in production use proper embeddings
        let mut vector = vec![0.0; self.dimension];
        let words: Vec<&str> = text.to_lowercase().split_whitespace().collect();
        
        for (i, word) in words.iter().enumerate() {
            let hash = word.chars().fold(0, |acc, c| acc.wrapping_mul(31).wrapping_add(c as usize)) % self.dimension;
            vector[hash] += 1.0 / (i + 1) as f32;
        }
        
        // Normalize
        let magnitude: f32 = vector.iter().map(|x| x * x).sum::<f32>().sqrt();
        if magnitude > 0.0 {
            for val in &mut vector {
                *val /= magnitude;
            }
        }
        
        vector
    }
}

#[cfg(feature = "sqlite")]
#[async_trait]
impl VectorStore for SQLiteVectorStore {
    async fn add_document(&mut self, content: &str) -> anyhow::Result<String> {
        let id = Uuid::new_v4().to_string();
        let vector = self.text_to_vector(content);
        self.add_vector(&id, vector, content).await?;
        Ok(id)
    }

    async fn add_vector(&mut self, id: &str, vector: Vec<f32>, content: &str) -> anyhow::Result<()> {
        if vector.len() != self.dimension {
            return Err(anyhow::anyhow!(
                "Vector dimension {} does not match expected dimension {}",
                vector.len(),
                self.dimension
            ));
        }

        let vector_bytes = self.vector_to_bytes(&vector);
        
        sqlx::query(r#"
            INSERT OR REPLACE INTO vectors (id, content, vector)
            VALUES (?, ?, ?)
        "#)
        .bind(id)
        .bind(content)
        .bind(&vector_bytes)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    async fn find_similar(&self, query: &str, limit: usize) -> anyhow::Result<Vec<VectorSimilarity>> {
        let query_vector = self.text_to_vector(query);
        self.find_similar_by_vector(&query_vector, limit).await
    }

    async fn find_similar_by_vector(&self, query_vector: &[f32], limit: usize) -> anyhow::Result<Vec<VectorSimilarity>> {
        let rows = sqlx::query(r#"SELECT id, content, vector FROM vectors"#)
            .fetch_all(&self.pool)
            .await?;

        let mut similarities: Vec<VectorSimilarity> = Vec::new();

        for row in rows {
            let vector_bytes: Vec<u8> = row.get("vector");
            let vector = self.bytes_to_vector(&vector_bytes);
            let similarity = self.cosine_similarity(query_vector, &vector);
            
            similarities.push(VectorSimilarity {
                id: row.get("id"),
                content: row.get("content"),
                similarity_score: similarity,
            });
        }

        // Sort by similarity score (highest first)
        similarities.sort_by(|a, b| b.similarity_score.partial_cmp(&a.similarity_score).unwrap());
        similarities.truncate(limit);

        Ok(similarities)
    }

    async fn remove_document(&mut self, id: &str) -> anyhow::Result<bool> {
        let result = sqlx::query(r#"DELETE FROM vectors WHERE id = ?"#)
            .bind(id)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
    }

    async fn get_document_count(&self) -> usize {
        sqlx::query_scalar(r#"SELECT COUNT(*) FROM vectors"#)
            .fetch_one(&self.pool)
            .await
            .unwrap_or(0)
    }
}