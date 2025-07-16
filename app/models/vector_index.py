from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class VectorIndex(Base):
    __tablename__ = 'vector_index'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))
    vector = Column(JSON)  # Store as list or use a vector extension
    metadata = Column(JSON)
    created_at = Column(DateTime)