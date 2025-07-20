use async_trait::async_trait;
use dashmap::DashMap;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeEntity {
    pub id: String,
    pub entity_type: String,
    pub properties: Vec<(String, String)>,
}

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
