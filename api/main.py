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
    answer: str
    id: int
    created_at: datetime

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
    db: Session = Depends(get_db),
    x_api_key: str = Depends(verify_api_key),
    request: Request = None
):
    if not reasoning_agent:
        raise HTTPException(status_code=500, detail="Rust extension not loaded")
    try:
        LLM_CALLS.labels(req.model).inc()
        answer = reasoning_agent.call_openai(
            req.prompt, req.model, req.max_tokens, req.temperature
        )
    except Exception as e:
        LLM_ERRORS.labels(req.model).inc()
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")
    record = TaskRecord(
        prompt=req.prompt,
        model=req.model,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        answer=answer,
        api_key=x_api_key
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    DB_WRITES.inc()
    return TaskResponse(answer=record.answer, id=record.id, created_at=record.created_at)

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
# - Ready for extension: OAuth2, async queue, Prometheus, etc.