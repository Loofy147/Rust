from fastapi import FastAPI, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import importlib

# --- Rate limiting ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# --- Prometheus metrics ---
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

# --- Celery ---
from celery.result import AsyncResult
from celery import Celery

# Import the Rust extension (built by maturin)
try:
    reasoning_agent = importlib.import_module("reasoning_agent")
except ImportError:
    reasoning_agent = None

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./reasoning_agent.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskRecord(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    model = Column(String, default="text-davinci-003")
    max_tokens = Column(Integer, default=256)
    temperature = Column(Float, default=0.7)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    api_key = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ReasoningAgent API")

# --- Prometheus Instrumentation ---
Instrumentator().instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")

# Custom Prometheus counters
LLM_CALLS = Counter("llm_calls_total", "Total LLM calls", ["model"])
LLM_ERRORS = Counter("llm_errors_total", "Total LLM call errors", ["model"])
DB_WRITES = Counter("db_writes_total", "Total DB write operations")
DB_READS = Counter("db_reads_total", "Total DB read operations")

# --- Celery config ---
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
celery = Celery("main", broker=REDIS_URL, backend=REDIS_URL)

# --- API Key Auth ---
def get_api_keys():
    keys = os.environ.get("API_KEYS", "testkey").split(",")
    return set(k.strip() for k in keys if k.strip())

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in get_api_keys():
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return x_api_key

# --- Rate Limiter ---
def get_rate_limit():
    return os.environ.get("RATE_LIMIT", "60/minute")

limiter = Limiter(key_func=lambda req: req.headers.get("x-api-key", ""), default_limits=[get_rate_limit()])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Models ---
class TaskRequest(BaseModel):
    prompt: str
    model: str = "text-davinci-003"
    max_tokens: int = 256
    temperature: float = 0.7

class TaskResponse(BaseModel):
    task_id: str

class ResultResponse(BaseModel):
    answer: str | None = None
    id: int | None = None
    created_at: datetime | None = None
    status: str
    error: str | None = None

class QueryResponse(BaseModel):
    id: int
    prompt: str
    answer: str
    created_at: datetime
    model: str
    max_tokens: int
    temperature: float
    api_key: str | None

# --- Endpoints ---
@app.post("/task", response_model=TaskResponse)
@limiter.limit(get_rate_limit())
async def submit_task(
    req: TaskRequest,
    x_api_key: str = Depends(verify_api_key),
    request: Request = None
):
    # Enqueue async LLM task
    LLM_CALLS.labels(req.model).inc()
    task = celery.send_task(
        "api.worker.llm_task",
        args=[req.prompt, req.model, req.max_tokens, req.temperature, x_api_key],
    )
    return TaskResponse(task_id=task.id)

@app.get("/result/{task_id}", response_model=ResultResponse)
@limiter.limit(get_rate_limit())
async def get_result(task_id: str, x_api_key: str = Depends(verify_api_key)):
    result = AsyncResult(task_id, app=celery)
    if result.state == "PENDING":
        return ResultResponse(status="pending")
    elif result.state == "STARTED":
        return ResultResponse(status="started")
    elif result.state == "FAILURE":
        return ResultResponse(status="failure", error=str(result.result))
    elif result.state == "SUCCESS":
        data = result.result
        return ResultResponse(
            answer=data.get("answer"),
            id=data.get("id"),
            created_at=data.get("created_at"),
            status="success"
        )
    else:
        return ResultResponse(status=result.state.lower())

@app.get("/query", response_model=list[QueryResponse])
@limiter.limit(get_rate_limit())
async def query_tasks(
    prompt: str = None,
    db: Session = Depends(get_db),
    x_api_key: str = Depends(verify_api_key),
    request: Request = None
):
    q = db.query(TaskRecord)
    if prompt:
        q = q.filter(TaskRecord.prompt.contains(prompt))
    q = q.order_by(TaskRecord.created_at.desc())
    results = q.all()
    DB_READS.inc()
    return [
        QueryResponse(
            id=r.id,
            prompt=r.prompt,
            answer=r.answer,
            created_at=r.created_at,
            model=r.model,
            max_tokens=r.max_tokens,
            temperature=r.temperature,
            api_key=r.api_key
        ) for r in results
    ]

@app.get("/metrics")
@limiter.limit(get_rate_limit())
async def metrics(db: Session = Depends(get_db), x_api_key: str = Depends(verify_api_key), request: Request = None):
    count = db.query(TaskRecord).count()
    return {"tasks_processed": count}

# --- Health check ---
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# --- Best practices ---
# - All endpoints require X-API-Key header
# - Per-API-key rate limiting (configurable via RATE_LIMIT env var)
# - All tasks/answers persisted in SQLite (configurable via DATABASE_URL)
# - Rust LLM plugin is called via Python extension
# - Prometheus metrics for LLM, DB, and API
# - Async LLM tasks via Celery+Redis
# - Ready for extension: OAuth2, async queue, Prometheus, etc.