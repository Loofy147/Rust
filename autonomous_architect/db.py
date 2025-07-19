import sqlite3

def init_db(db_path="architecture_graph.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        id TEXT PRIMARY KEY,
        type TEXT,
        path TEXT,
        content_hash TEXT,
        metadata TEXT,
        last_modified TIMESTAMP,
        quality_score REAL,
        learning_context TEXT
    );
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        source_id TEXT,
        target_id TEXT,
        relationship_type TEXT,
        strength REAL,
        metadata TEXT,
        created_at TIMESTAMP
    );
    ''')
    conn.commit()
    conn.close()