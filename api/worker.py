import os
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import importlib
from llm_plugins import get_plugin
from vector_store.chroma_store import ChromaVectorStore

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./reasoning_agent.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
celery = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

from api.main import TaskRecord, Base

vector_store = ChromaVectorStore()

@celery.task(bind=True)
def llm_task(self, prompt, model, max_tokens, temperature, api_key, provider="openai"):
    session = SessionLocal()
    try:
        plugin = get_plugin(provider)
        answer = plugin.call(prompt, model, max_tokens, temperature)
        record = TaskRecord(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            answer=answer,
            api_key=api_key,
            created_at=datetime.utcnow()
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        # Upsert answer to vector store
        vector_store.upsert(
            str(record.id),
            answer,
            metadata={"prompt": prompt, "model": model, "provider": provider}
        )
        return {"answer": answer, "id": record.id, "created_at": str(record.created_at)}
    except Exception as e:
        session.rollback()
        raise self.retry(exc=e, countdown=5, max_retries=3)
    finally:
        session.close()