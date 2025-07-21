import aiosqlite
import asyncio
import logging
from typing import Dict, Any, Optional, List, Set, Callable
from datetime import datetime
from collections import defaultdict
from dataclasses import asdict
import json
import importlib.util
import os
from abc import ABC, abstractmethod

class Entity:
    pass
class Relationship:
    pass
class EntityType:
    pass
class RelationshipType:
    pass

class ReasoningRule(ABC):
    name: str
    @abstractmethod
    def applies_to_context(self, query_context: Dict[str, Any]) -> bool:
        pass
    @abstractmethod
    async def execute(self, engine: 'AsyncKnowledgeGraphEngine', query_context: Dict[str, Any]) -> Dict[str, Any]:
        pass

class AsyncKnowledgeGraphEngine:
    def __init__(self, db_path: str = "knowledge_graph.db"):
        self.db_path = db_path
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.entity_type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self.relationship_type_index: Dict[RelationshipType, Set[str]] = defaultdict(set)
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("AsyncKnowledgeGraphEngine")
        self.rules: Dict[str, ReasoningRule] = {}

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

    async def load_rule(self, rule_path: str) -> str:
        """Dynamically load a rule from a Python file."""
        spec = importlib.util.spec_from_file_location("dynamic_rule", rule_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, ReasoningRule) and obj is not ReasoningRule:
                rule = obj()
                self.rules[rule.name] = rule
                self.logger.info(f"Loaded rule: {rule.name}")
                return rule.name
        raise ValueError("No ReasoningRule found in module")

    async def unload_rule(self, rule_name: str) -> bool:
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.info(f"Unloaded rule: {rule_name}")
            return True
        return False

    async def list_rules(self) -> List[str]:
        return list(self.rules.keys())

    async def reload_rules_and_listeners(self):
        # For demo: reload all rules from a 'rules/' directory
        self.rules.clear()
        rules_dir = os.path.join(os.path.dirname(__file__), 'rules')
        if os.path.isdir(rules_dir):
            for fname in os.listdir(rules_dir):
                if fname.endswith('.py'):
                    try:
                        await self.load_rule(os.path.join(rules_dir, fname))
                    except Exception as e:
                        self.logger.error(f"Failed to load rule {fname}: {e}")

    async def execute_reasoning(self, query: str, context: Dict[str, Any] = None, rules: List[str] = None, trace: bool = False) -> Dict[str, Any]:
        self.logger.info(f"Reasoning executed for query: {query}")
        context = context or {}
        trace_log = []
        inferred_facts = []
        confidence_scores = {}
        for rule_name, rule in self.rules.items():
            if rules and rule_name not in rules:
                continue
            if rule.applies_to_context(context):
                result = await rule.execute(self, context)
                inferred_facts.extend(result.get('facts', []))
                confidence_scores.update(result.get('confidence', {}))
                if trace:
                    trace_log.append({"rule": rule_name, "result": result, "timestamp": datetime.now().isoformat()})
        return {
            "query": query,
            "inferred_facts": inferred_facts,
            "confidence_scores": confidence_scores,
            "trace": trace_log if trace else None
        }