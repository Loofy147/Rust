use async_trait::async_trait;
use dashmap::DashMap;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::types::KnowledgeEntity;

/// Trait for knowledge graph operations
#[async_trait]
pub trait KnowledgeGraph: Send + Sync {
    async fn add_entity(&mut self, entity: KnowledgeEntity) -> anyhow::Result<()>;
    async fn get_entity(&self, id: &str) -> anyhow::Result<Option<KnowledgeEntity>>;
    async fn query_entities(&self, query: &str) -> anyhow::Result<Vec<KnowledgeEntity>>;
    async fn add_relationship(&mut self, from_id: &str, to_id: &str, relationship_type: &str) -> anyhow::Result<()>;
    async fn get_relationships(&self, entity_id: &str) -> anyhow::Result<Vec<Relationship>>;
    async fn remove_entity(&mut self, id: &str) -> anyhow::Result<bool>;
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Relationship {
    pub id: String,
    pub from_id: String,
    pub to_id: String,
    pub relationship_type: String,
    pub properties: Vec<(String, String)>,
}

/// In-memory knowledge graph implementation using DashMap for thread safety
pub struct InMemoryKnowledgeGraph {
    entities: Arc<DashMap<String, KnowledgeEntity>>,
    relationships: Arc<DashMap<String, Relationship>>,
    entity_relationships: Arc<DashMap<String, Vec<String>>>, // entity_id -> relationship_ids
}

impl InMemoryKnowledgeGraph {
    pub fn new() -> Self {
        Self {
            entities: Arc::new(DashMap::new()),
            relationships: Arc::new(DashMap::new()),
            entity_relationships: Arc::new(DashMap::new()),
        }
    }

    pub fn with_sample_data() -> Self {
        let kg = Self::new();
        
        // Add some sample knowledge entities
        let entities = vec![
            KnowledgeEntity {
                id: "renewable_energy_001".to_string(),
                entity_type: "concept".to_string(),
                properties: vec![
                    ("name".to_string(), "Renewable Energy".to_string()),
                    ("definition".to_string(), "Energy from natural resources that are replenished naturally".to_string()),
                    ("examples".to_string(), "Solar, Wind, Hydro, Geothermal".to_string()),
                ],
            },
            KnowledgeEntity {
                id: "solar_power_001".to_string(),
                entity_type: "technology".to_string(),
                properties: vec![
                    ("name".to_string(), "Solar Power".to_string()),
                    ("efficiency".to_string(), "15-22% for commercial panels".to_string()),
                    ("cost_trend".to_string(), "Decreasing rapidly since 2010".to_string()),
                ],
            },
            KnowledgeEntity {
                id: "climate_change_001".to_string(),
                entity_type: "phenomenon".to_string(),
                properties: vec![
                    ("name".to_string(), "Climate Change".to_string()),
                    ("cause".to_string(), "Greenhouse gas emissions from human activities".to_string()),
                    ("impact".to_string(), "Rising temperatures, sea levels, extreme weather".to_string()),
                ],
            },
        ];

        for entity in entities {
            kg.entities.insert(entity.id.clone(), entity);
        }

        kg
    }
}

#[async_trait]
impl KnowledgeGraph for InMemoryKnowledgeGraph {
    async fn add_entity(&mut self, entity: KnowledgeEntity) -> anyhow::Result<()> {
        self.entities.insert(entity.id.clone(), entity);
        Ok(())
    }

    async fn get_entity(&self, id: &str) -> anyhow::Result<Option<KnowledgeEntity>> {
        Ok(self.entities.get(id).map(|e| e.clone()))
    }

    async fn query_entities(&self, query: &str) -> anyhow::Result<Vec<KnowledgeEntity>> {
        let query_lower = query.to_lowercase();
        let mut results = Vec::new();

        for entity in self.entities.iter() {
            // Simple text matching - in production you'd want more sophisticated search
            let matches = entity.entity_type.to_lowercase().contains(&query_lower)
                || entity.properties.iter().any(|(key, value)| {
                    key.to_lowercase().contains(&query_lower) 
                    || value.to_lowercase().contains(&query_lower)
                });

            if matches {
                results.push(entity.clone());
            }
        }

        // Limit results to prevent overwhelming the LLM
        results.truncate(10);
        Ok(results)
    }

    async fn add_relationship(&mut self, from_id: &str, to_id: &str, relationship_type: &str) -> anyhow::Result<()> {
        let relationship_id = Uuid::new_v4().to_string();
        let relationship = Relationship {
            id: relationship_id.clone(),
            from_id: from_id.to_string(),
            to_id: to_id.to_string(),
            relationship_type: relationship_type.to_string(),
            properties: vec![],
        };

        self.relationships.insert(relationship_id.clone(), relationship);
        
        // Update entity relationship mappings
        self.entity_relationships
            .entry(from_id.to_string())
            .or_insert_with(Vec::new)
            .push(relationship_id.clone());
        
        self.entity_relationships
            .entry(to_id.to_string())
            .or_insert_with(Vec::new)
            .push(relationship_id);

        Ok(())
    }

    async fn get_relationships(&self, entity_id: &str) -> anyhow::Result<Vec<Relationship>> {
        let mut relationships = Vec::new();
        
        if let Some(relationship_ids) = self.entity_relationships.get(entity_id) {
            for rel_id in relationship_ids.iter() {
                if let Some(relationship) = self.relationships.get(rel_id) {
                    relationships.push(relationship.clone());
                }
            }
        }

        Ok(relationships)
    }

    async fn remove_entity(&mut self, id: &str) -> anyhow::Result<bool> {
        // Remove the entity
        let removed = self.entities.remove(id).is_some();
        
        // Remove associated relationships
        if let Some(relationship_ids) = self.entity_relationships.remove(id) {
            for rel_id in relationship_ids.1 {
                self.relationships.remove(&rel_id);
            }
        }

        Ok(removed)
    }
}

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