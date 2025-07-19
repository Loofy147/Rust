use async_trait::async_trait;
use sqlx::Row;
use uuid::Uuid;
use crate::storage::memory::{KnowledgeGraph, KnowledgeEntity, Relationship};
use crate::storage::vector_store::{VectorStore, VectorSimilarity};

/// SQLite-based persistent knowledge graph
#[cfg(feature = "sqlite")]
pub struct SQLiteKnowledgeGraph {
    pool: sqlx::SqlitePool,
}

#[cfg(feature = "sqlite")]
impl SQLiteKnowledgeGraph {
    pub async fn new(database_url: &str) -> anyhow::Result<Self> {
        let pool = sqlx::SqlitePool::connect(database_url).await?;

        // Create tables if they don't exist
        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                properties TEXT NOT NULL
            )
        "#)
        .execute(&pool)
        .await?;

        sqlx::query(r#"
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                properties TEXT NOT NULL,
                FOREIGN KEY (from_id) REFERENCES entities (id),
                FOREIGN KEY (to_id) REFERENCES entities (id)
            )
        "#)
        .execute(&pool)
        .await?;

        Ok(Self { pool })
    }
}

#[cfg(feature = "sqlite")]
#[async_trait]
impl KnowledgeGraph for SQLiteKnowledgeGraph {
    async fn add_entity(&mut self, entity: KnowledgeEntity) -> anyhow::Result<()> {
        let properties_json = serde_json::to_string(&entity.properties)?;

        sqlx::query(r#"
            INSERT OR REPLACE INTO entities (id, entity_type, properties)
            VALUES (?, ?, ?)
        "#)
        .bind(&entity.id)
        .bind(&entity.entity_type)
        .bind(&properties_json)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    async fn get_entity(&self, id: &str) -> anyhow::Result<Option<KnowledgeEntity>> {
        let row = sqlx::query(r#"
            SELECT id, entity_type, properties FROM entities WHERE id = ?
        "#)
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        if let Some(row) = row {
            let properties: Vec<(String, String)> = serde_json::from_str(&row.get::<String, _>("properties"))?;
            Ok(Some(KnowledgeEntity {
                id: row.get("id"),
                entity_type: row.get("entity_type"),
                properties,
            }))
        } else {
            Ok(None)
        }
    }

    async fn query_entities(&self, query: &str) -> anyhow::Result<Vec<KnowledgeEntity>> {
        let rows = sqlx::query(r#"
            SELECT id, entity_type, properties FROM entities
            WHERE entity_type LIKE ? OR properties LIKE ?
            LIMIT 10
        "#)
        .bind(format!("%{}%", query))
        .bind(format!("%{}%", query))
        .fetch_all(&self.pool)
        .await?;

        let mut entities = Vec::new();
        for row in rows {
            let properties: Vec<(String, String)> = serde_json::from_str(&row.get::<String, _>("properties"))?;
            entities.push(KnowledgeEntity {
                id: row.get("id"),
                entity_type: row.get("entity_type"),
                properties,
            });
        }

        Ok(entities)
    }

    async fn add_relationship(&mut self, from_id: &str, to_id: &str, relationship_type: &str) -> anyhow::Result<()> {
        let relationship_id = Uuid::new_v4().to_string();
        let properties_json = serde_json::to_string(&Vec::<(String, String)>::new())?;

        sqlx::query(r#"
            INSERT INTO relationships (id, from_id, to_id, relationship_type, properties)
            VALUES (?, ?, ?, ?, ?)
        "#)
        .bind(&relationship_id)
        .bind(from_id)
        .bind(to_id)
        .bind(relationship_type)
        .bind(&properties_json)
        .execute(&self.pool)
        .await?;

        Ok(())
    }

    async fn get_relationships(&self, entity_id: &str) -> anyhow::Result<Vec<Relationship>> {
        let rows = sqlx::query(r#"
            SELECT id, from_id, to_id, relationship_type, properties FROM relationships
            WHERE from_id = ? OR to_id = ?
        "#)
        .bind(entity_id)
        .bind(entity_id)
        .fetch_all(&self.pool)
        .await?;

        let mut relationships = Vec::new();
        for row in rows {
            let properties: Vec<(String, String)> = serde_json::from_str(&row.get::<String, _>("properties"))?;
            relationships.push(Relationship {
                id: row.get("id"),
                from_id: row.get("from_id"),
                to_id: row.get("to_id"),
                relationship_type: row.get("relationship_type"),
                properties,
            });
        }

        Ok(relationships)
    }

    async fn remove_entity(&mut self, id: &str) -> anyhow::Result<bool> {
        let result = sqlx::query(r#"DELETE FROM entities WHERE id = ?"#)
            .bind(id)
            .execute(&self.pool)
            .await?;

        // Also remove relationships
        sqlx::query(r#"DELETE FROM relationships WHERE from_id = ? OR to_id = ?"#)
            .bind(id)
            .bind(id)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
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
        let lower_text = text.to_lowercase();
        let words: Vec<&str> = lower_text.split_whitespace().collect();

        for (i, word) in words.iter().enumerate() {
            let hash = word.chars().fold(0, |acc: usize, c| acc.wrapping_mul(31).wrapping_add(c as usize)) % self.dimension;
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
        let count: i64 = sqlx::query_scalar(r#"SELECT COUNT(*) FROM vectors"#)
            .fetch_one(&self.pool)
            .await
            .unwrap_or(0);
        count as usize
    }
}
