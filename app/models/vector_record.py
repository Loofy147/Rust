from sqlalchemy import Column, String, Integer, JSON, DateTime
from .base import Base

class VectorRecord(Base):
    __tablename__ = 'vectors'
    id = Column(String, primary_key=True)
    tenant = Column(String)
    vector_type = Column(String)
    dimensions = Column(Integer)
    data = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime)
    checksum = Column(String)
