import aiosqlite
import asyncio
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from collections import defaultdict
from dataclasses import asdict
from . import Entity, Relationship, EntityType, RelationshipType
import json

class AsyncKnowledgeGraphEngine:
    def __init__(self, db_path: str = "knowledge_graph.db"):
        self.db_path = db_path
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.entity_type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self.relationship_type_index: Dict[RelationshipType, Set[str]] = defaultdict(set)
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("AsyncKnowledgeGraphEngine")

    async def _initialize_database(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                properties TEXT,
                metadata TEXT,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                confidence REAL DEFAULT 0.8,
                source_agent TEXT,
                version INTEGER DEFAULT 1
            )''')
            await conn.execute('''CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                confidence REAL DEFAULT 0.8,
                context TEXT,
                temporal_start TIMESTAMP,
                temporal_end TIMESTAMP,
                conditions TEXT,
                evidence TEXT,
                created_at TIMESTAMP,
                last_validated TIMESTAMP,
                validation_count INTEGER DEFAULT 0
            )''')
            await conn.commit()
        self.logger.info("Database initialized")

    async def add_entity(self, entity: Entity) -> str:
        async with self.lock:
            self.entities[entity.id] = entity
            self.entity_type_index[entity.type].add(entity.id)
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    'INSERT OR REPLACE INTO entities (id, type, name, properties, metadata, created_at, last_accessed, access_count, confidence, source_agent, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        entity.id, entity.type.value, entity.name,
                        json.dumps(entity.properties), json.dumps(entity.metadata),
                        entity.created_at.isoformat(), entity.last_accessed.isoformat(),
                        entity.access_count, entity.confidence, entity.source_agent, entity.version
                    )
                )
                await conn.commit()
            self.logger.info(f"Entity added: {entity.id}")
            return entity.id

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        async with self.lock:
            return self.entities.get(entity_id)

    async def add_relationship(self, relationship: Relationship) -> str:
        async with self.lock:
            self.relationships[relationship.id] = relationship
            self.relationship_type_index[relationship.type].add(relationship.id)
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    'INSERT OR REPLACE INTO relationships (id, source_id, target_id, type, weight, confidence, context, temporal_start, temporal_end, conditions, evidence, created_at, last_validated, validation_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        relationship.id, relationship.source_id, relationship.target_id, relationship.type.value,
                        relationship.weight, relationship.confidence, json.dumps(relationship.context),
                        relationship.temporal_validity[0].isoformat() if relationship.temporal_validity else None,
                        relationship.temporal_validity[1].isoformat() if relationship.temporal_validity else None,
                        json.dumps(relationship.conditions), json.dumps(relationship.evidence),
                        relationship.created_at.isoformat(), relationship.last_validated.isoformat(), relationship.validation_count
                    )
                )
                await conn.commit()
            self.logger.info(f"Relationship added: {relationship.id}")
            return relationship.id

    async def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        async with self.lock:
            return self.relationships.get(rel_id)

    async def query_entities(self, entity_type: Optional[EntityType] = None, name_pattern: Optional[str] = None) -> List[Entity]:
        async with self.lock:
            if entity_type:
                candidate_ids = self.entity_type_index[entity_type]
            else:
                candidate_ids = set(self.entities.keys())
            results = []
            for entity_id in candidate_ids:
                entity = self.entities[entity_id]
                if name_pattern and name_pattern.lower() not in entity.name.lower():
                    continue
                results.append(entity)
            return results

    async def execute_reasoning(self, query: str) -> Dict[str, Any]:
        # Placeholder for async reasoning logic
        self.logger.info(f"Reasoning executed for query: {query}")
        return {"query": query, "result": "Reasoning not implemented"}