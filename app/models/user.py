from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    org_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))
    role = Column(String, default='user')
    created_at = Column(DateTime)
    updated_at = Column(DateTime)