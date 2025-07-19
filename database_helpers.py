
import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

def get_db_connection(db_path: str):
    """Create and return a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_knowledge_graph_db(db_path: str):
    """Initialize the Knowledge Graph database tables."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Entities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            properties TEXT,
            created_at TEXT,
            updated_at TEXT,
            access_count INTEGER DEFAULT 0
        )
    ''')

    # Relationships table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT,
            target_id TEXT,
            relationship_type TEXT,
            properties TEXT,
            strength REAL DEFAULT 1.0,
            created_at TEXT,
            FOREIGN KEY (source_id) REFERENCES entities (id),
            FOREIGN KEY (target_id) REFERENCES entities (id)
        )
    ''')

    # Outcomes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT,
            outcome_type TEXT,
            outcome_data TEXT,
            success BOOLEAN,
            timestamp TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )
    ''')

    # Expectations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expectations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT,
            expectation_type TEXT,
            expectation_data TEXT,
            met BOOLEAN,
            timestamp TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )
    ''')

    # Context table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT,
            context_type TEXT,
            context_data TEXT,
            relevance_score REAL DEFAULT 1.0,
            timestamp TEXT,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )
    ''')

    conn.commit()
    conn.close()

def insert_or_replace_entity(db_path: str, entity_id: str, entity_type: str, name: str, properties: Dict, created_at: str, updated_at: str) -> bool:
    """Insert or replace an entity in the database."""
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO entities (id, type, name, properties, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (entity_id, entity_type, name, json.dumps(properties),
              created_at, updated_at))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting/replacing entity: {e}")
        return False

def insert_relationship(db_path: str, source_id: str, target_id: str, relationship_type: str, properties: Dict, strength: float, created_at: str) -> bool:
    """Insert a relationship into the database."""
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO relationships (source_id, target_id, relationship_type, properties, strength, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (source_id, target_id, relationship_type,
              json.dumps(properties), strength, created_at))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting relationship: {e}")
        return False

def get_entity(db_path: str, entity_id: str) -> Optional[Dict]:
    """Retrieve an entity by its ID from the database."""
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            # Return as a dictionary, including json-parsed properties
            entity_dict = dict(row)
            entity_dict['properties'] = json.loads(entity_dict['properties'])
            return entity_dict
        return None
    except Exception as e:
        print(f"Error retrieving entity {entity_id}: {e}")
        return None

def get_relationships(db_path: str, source_id: Optional[str] = None, target_id: Optional[str] = None, relationship_type: Optional[str] = None) -> List[Dict]:
    """Retrieve relationships based on criteria."""
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM relationships WHERE 1=1"
        params = []
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        if relationship_type:
            query += " AND relationship_type = ?"
            params.append(relationship_type)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        relationships_list = []
        for row in rows:
            rel_dict = dict(row)
            rel_dict['properties'] = json.loads(rel_dict['properties'])
            relationships_list.append(rel_dict)
        return relationships_list
    except Exception as e:
        print(f"Error retrieving relationships: {e}")
        return []

# Add more helper functions for other tables (outcomes, expectations, context)
# and for deletion, updates, etc.
