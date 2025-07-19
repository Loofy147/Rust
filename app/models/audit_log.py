from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))
    action = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime)