import sqlite3
from typing import Optional, List, Dict
import os

class SQLiteKG:
    def __init__(self, db_path: str = "./kg.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS kg_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                properties TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS kg_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source INTEGER NOT NULL,
                target INTEGER NOT NULL,
                label TEXT NOT NULL,
                properties TEXT,
                FOREIGN KEY(source) REFERENCES kg_nodes(id),
                FOREIGN KEY(target) REFERENCES kg_nodes(id)
            )
        """)
        self.conn.commit()

    def upsert_node(self, label: str, properties: str = "") -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO kg_nodes (label, properties) VALUES (?, ?)", (label, properties))
        self.conn.commit()
        return c.lastrowid

    def upsert_edge(self, source: int, target: int, label: str, properties: str = "") -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO kg_edges (source, target, label, properties) VALUES (?, ?, ?, ?)", (source, target, label, properties))
        self.conn.commit()
        return c.lastrowid

    def query_nodes(self, label: Optional[str] = None) -> List[Dict]:
        c = self.conn.cursor()
        if label:
            c.execute("SELECT id, label, properties FROM kg_nodes WHERE label = ?", (label,))
        else:
            c.execute("SELECT id, label, properties FROM kg_nodes")
        return [dict(id=row[0], label=row[1], properties=row[2]) for row in c.fetchall()]

    def query_edges(self, source: Optional[int] = None, target: Optional[int] = None, label: Optional[str] = None) -> List[Dict]:
        c = self.conn.cursor()
        query = "SELECT id, source, target, label, properties FROM kg_edges WHERE 1=1"
        params = []
        if source is not None:
            query += " AND source = ?"
            params.append(source)
        if target is not None:
            query += " AND target = ?"
            params.append(target)
        if label is not None:
            query += " AND label = ?"
            params.append(label)
        c.execute(query, tuple(params))
        return [dict(id=row[0], source=row[1], target=row[2], label=row[3], properties=row[4]) for row in c.fetchall()]