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

Base.metadata.create_all(bind=engine)

# --- Rate Limiter Setup ---
rate_limit = os.environ.get("RATE_LIMIT", "60/minute")
limiter = Limiter(key_func=lambda request: request.headers.get("x-api-key", "nokey"))
app = FastAPI(title="ReasoningAgent API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Key Auth ---
def get_api_keys():
    keys = os.environ.get("API_KEYS", "")
    return set(k.strip() for k in keys.split(",") if k.strip())

def api_key_auth(x_api_key: str = Header(...)):
    valid_keys = get_api_keys()
    if not valid_keys:
        raise HTTPException(status_code=500, detail="API key auth not configured")
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

class TaskRequest(BaseModel):
    prompt: str
    model: str = "text-davinci-003"
    max_tokens: int = 256
    temperature: float = 0.7

class TaskResponse(BaseModel):
    answer: str

class QueryResponse(BaseModel):
    id: int
    prompt: str
    answer: str
    created_at: datetime

@app.post("/task", response_model=TaskResponse)
@limiter.limit(rate_limit)
def submit_task(
    req: TaskRequest,
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_auth)
):
    if not reasoning_agent:
        raise HTTPException(status_code=500, detail="Rust extension not loaded")
    try:
        answer = reasoning_agent.call_openai(
            req.prompt, req.model, req.max_tokens, req.temperature
        )
        # Store in DB
        record = TaskRecord(
            prompt=req.prompt,
            model=req.model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            answer=answer,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return TaskResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
@limiter.limit(rate_limit)
def metrics(
    request: Request,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_auth)
):
    count = db.query(TaskRecord).count()
    return {"status": "ok", "tasks_processed": count}

@app.get("/query", response_model=list[QueryResponse])
@limiter.limit(rate_limit)
def query(
    request: Request,
    prompt: str = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(api_key_auth)
):
    q = db.query(TaskRecord)
    if prompt:
        q = q.filter(TaskRecord.prompt.contains(prompt))
    results = q.order_by(TaskRecord.created_at.desc()).limit(20).all()
    return [
        QueryResponse(
            id=r.id, prompt=r.prompt, answer=r.answer, created_at=r.created_at
        ) for r in results
    ]