import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import numpy as np
import aioredis
import hashlib
import jwt
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from prometheus_client import Counter, Gauge, start_http_server
from app.models.base import Base
from app.models.vector_record import VectorRecord
from enum import Enum
from dataclasses import dataclass, field
import time
from .retry import retry_with_exponential_backoff

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("OrchestratorAI")

# --- Prometheus Metrics ---
TASKS_PROCESSED = Counter('orchestrator_tasks_processed', 'Tasks processed by orchestrator')
VECTORS_STORED = Counter('orchestrator_vectors_stored', 'Vectors stored')
ORCH_UPTIME = Gauge('orchestrator_uptime', 'Orchestrator uptime')

# --- Database ---
DB_URL = os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///orchestrator.db')
engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# --- Redis ---
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
QUEUE_NAME = os.environ.get('REDIS_QUEUE', 'agentsys-tasks')

# --- JWT Auth ---
JWT_SECRET = os.environ.get('JWT_SECRET', 'changemejwtsecret')
JWT_ALGO = 'HS256'

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

class OrchestratorAI:
    def __init__(self, project_goal: str = "Build a robust, scalable, and intelligent agent system."):
        self.logger = logging.getLogger("OrchestratorAI")
        self.project_goal = project_goal
        self.running = True
        self.agent_registry: Dict[str, Any] = {}
        self.redis = None
        self.db = None
        self.supervisor_task = None

    async def setup(self):
        self.redis = await aioredis.create_redis_pool(REDIS_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.db = AsyncSessionLocal
        start_http_server(9100)
        self.supervisor_task = asyncio.create_task(self.supervise())
        asyncio.create_task(self.run())
        logger.info("OrchestratorAI setup complete.")

    def register_agent(self, name: str, agent: Any):
        self.agent_registry[name] = agent
        self.logger.info(f"Registered agent: {name}")

    async def run(self):
        logger.info("OrchestratorAI running and listening for external tasks.")
        while self.running:
            try:
                task_json = await self.redis.blpop(QUEUE_NAME, timeout=1)
                if not task_json:
                    await asyncio.sleep(0.1)
                    continue
                _, data = task_json
                task_data = json.loads(data)
                await self.process_external_task(task_data)
            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}")
                await asyncio.sleep(2)

    @retry_with_exponential_backoff()
    async def process_external_task(self, task_data: Dict[str, Any]):
        try:
            token = task_data.get('jwt')
            tenant = 'default'
            if token:
                try:
                    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
                    tenant = payload.get('tenant', 'default')
                except Exception as e:
                    logger.warning(f"JWT decode failed: {e}")

            data = np.array(task_data['data'])
            vector_id = f"vec_{hashlib.md5(data.tobytes()).hexdigest()[:8]}_{int(datetime.now().timestamp())}"
            metadata = VectorMetadata(
                vector_id=vector_id,
                vector_type=task_data.get('vector_type', VectorType.EMBEDDING),
                dimensions=data.shape[1] if len(data.shape) > 1 else data.shape[0],
                creation_timestamp=datetime.now(),
                tenant=tenant
            )
            checksum = hashlib.sha256(data.tobytes()).hexdigest()
            metadata.checksum = checksum

            await self.store_vector(data, metadata)
            TASKS_PROCESSED.inc()
            logger.info(f"Processed vector {vector_id} for tenant {tenant}")

        except Exception as e:
            logger.error(f"External task processing error: {e}")

    async def store_vector(self, data: np.ndarray, metadata: VectorMetadata):
        record = VectorRecord(
            id=metadata.vector_id,
            tenant=metadata.tenant,
            vector_type=metadata.vector_type.value,
            dimensions=metadata.dimensions,
            data=data.tolist(),
            metadata={'extra': metadata.extra},
            created_at=metadata.creation_timestamp,
            checksum=metadata.checksum
        )
        async with self.db() as session:
            session.add(record)
            await session.commit()
        VECTORS_STORED.inc()

    async def supervise(self):
        while self.running:
            await asyncio.sleep(2)

    async def stop(self):
        self.running = False
        if self.supervisor_task:
            self.supervisor_task.cancel()
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
        if self.db:
            await self.db.close()
        logger.info("OrchestratorAI stopped.")

    def get_status(self):
        return {
            "running": self.running,
            "agents": list(self.agent_registry.keys())
        }
