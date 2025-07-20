from sqlalchemy import Column, String, Float, JSON, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Node(Base):
    __tablename__ = 'nodes'
    node_id = Column(String, primary_key=True)
    status = Column(String)
    last_seen = Column(Float)
    capabilities = Column(JSON)
    load = Column(Float)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    status = Column(String)
    node_id = Column(String)
    payload = Column(JSON)
    submitted_at = Column(Float)
    assigned_at = Column(Float)
    completed_at = Column(Float)
    result = Column(Text)