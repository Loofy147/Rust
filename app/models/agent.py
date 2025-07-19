from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class Agent(Base):
    __tablename__ = 'agents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))
    config = Column(JSON)
    status = Column(String, default='stopped')
    created_at = Column(DateTime)