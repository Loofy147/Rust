import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from queue import Queue
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
import aioredis
import hashlib
import jwt
from prometheus_client import Counter, Gauge, start_http_server

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("orchestrator")

# --- Prometheus Metrics ---
TASKS_PROCESSED = Counter('orchestrator_tasks_processed', 'Tasks processed by orchestrator')
VECTORS_STORED = Counter('orchestrator_vectors_stored', 'Vectors stored')
ORCH_UPTIME = Gauge('orchestrator_uptime', 'Orchestrator uptime')

# --- SQLAlchemy Async DB ---
Base = declarative_base()
DB_URL = os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///orchestrator.db')
engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

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

# --- Redis Queue ---
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
QUEUE_NAME = os.environ.get('REDIS_QUEUE', 'agentsys-tasks')

# --- JWT Auth ---
JWT_SECRET = os.environ.get('JWT_SECRET', 'changemejwtsecret')
JWT_ALGO = 'HS256'

# --- Vector Types ---
class VectorType(str, Enum):
    EMBEDDING = "embedding"
    FEATURE = "feature"

@dataclass
class VectorMetadata:
    vector_id: str
    vector_type: VectorType
    dimensions: int
    creation_timestamp: datetime
    tenant: str
    checksum: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

# --- Orchestrator ---
class AsyncOrchestrator:
    def __init__(self):
        self.redis = None
        self.db = None
        self.active = True
        self.metrics = {"tasks_processed": 0, "vectors_stored": 0, "uptime": datetime.now()}

    async def setup(self):
        self.redis = await aioredis.create_redis_pool(REDIS_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.db = AsyncSessionLocal()
        start_http_server(9100)  # Prometheus metrics
        logger.info("Orchestrator setup complete.")

    async def run(self):
        logger.info("Orchestrator started.")
        while self.active:
            try:
                task_json = await self.redis.blpop(QUEUE_NAME, timeout=5)
                if not task_json:
                    await asyncio.sleep(1)
                    continue
                _, data = task_json
                task = json.loads(data)
                await self.process_task(task)
            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}")
                await asyncio.sleep(2)

    async def process_task(self, task: Dict[str, Any]):
        try:
            # JWT/tenant extraction
            token = task.get('jwt')
            tenant = 'default'
            if token:
                try:
                    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
                    tenant = payload.get('tenant', 'default')
                except Exception as e:
                    logger.warning(f"JWT decode failed: {e}")
            # Vector processing (demo: embedding)
            data = np.array(task['data'])
            vector_id = f"vec_{hashlib.md5(data.tobytes()).hexdigest()[:8]}_{int(datetime.now().timestamp())}"
            metadata = VectorMetadata(
                vector_id=vector_id,
                vector_type=task.get('vector_type', VectorType.EMBEDDING),
                dimensions=data.shape[1] if len(data.shape) > 1 else data.shape[0],
                creation_timestamp=datetime.now(),
                tenant=tenant
            )
            checksum = hashlib.sha256(data.tobytes()).hexdigest()
            metadata.checksum = checksum
            await self.store_vector(data, metadata)
            self.metrics["tasks_processed"] += 1
            TASKS_PROCESSED.inc()
            logger.info(f"Processed vector {vector_id} for tenant {tenant}")
        except Exception as e:
            logger.error(f"Task processing error: {e}")

    async def store_vector(self, data: np.ndarray, metadata: VectorMetadata):
        record = VectorRecord(
            id=metadata.vector_id,
            tenant=metadata.tenant,
            vector_type=metadata.vector_type,
            dimensions=metadata.dimensions,
            data=data.tolist(),
            metadata=metadata.__dict__,
            created_at=metadata.creation_timestamp,
            checksum=metadata.checksum
        )
        async with self.db as session:
            session.add(record)
            await session.commit()
        self.metrics["vectors_stored"] += 1
        VECTORS_STORED.inc()

    async def shutdown(self):
        self.active = False
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
        if self.db:
            await self.db.close()
        logger.info("Orchestrator shutdown complete.")

# --- Entrypoint ---
if __name__ == "__main__":
    orchestrator = AsyncOrchestrator()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(orchestrator.setup())
    try:
        loop.run_until_complete(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("Shutting down orchestrator...")
        loop.run_until_complete(orchestrator.shutdown())