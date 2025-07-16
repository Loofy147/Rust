from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))
    type = Column(String)
    status = Column(String, default='pending')
    input = Column(JSON)
    output = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)