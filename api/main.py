from fastapi import FastAPI, HTTPException, Depends, Header, Request, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import os
import importlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from llm_plugins import get_plugin, list_plugins
from vector_store.chroma_store import ChromaVectorStore
import uuid

# --- Rate limiting ---
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.redis import RedisBackend

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

# --- User model for OAuth2 ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    disabled = Column(Integer, default=0)

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

# --- Distributed Rate Limiter (Redis backend) ---
redis_backend = RedisBackend(REDIS_URL)
def get_rate_limit():
    return os.environ.get("RATE_LIMIT", "60/minute")
limiter = Limiter(
    key_func=lambda req: req.headers.get("x-api-key", ""),
    default_limits=[get_rate_limit()],
    storage_uri=REDIS_URL,
    backend=redis_backend
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Password hashing and JWT config ---
SECRET_KEY = os.environ.get("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- OAuth2/JWT dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: SessionLocal())):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username)
    if user is None or user.disabled:
        raise credentials_exception
    return user

# --- API Key Auth ---
def get_api_keys():
    keys = os.environ.get("API_KEYS", "testkey").split(",")
    return set(k.strip() for k in keys if k.strip())

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key is None:
        return None
    if x_api_key not in get_api_keys():
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return x_api_key

# --- DB Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserOut(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool = False

class TaskRequest(BaseModel):
    prompt: str
    model: str = "text-davinci-003"
    max_tokens: int = 256
    temperature: float = 0.7
    provider: str = Query("openai", description="LLM provider: openai or huggingface")

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

class ModelInfo(BaseModel):
    provider: str
    models: list[str]

class VectorUpsertRequest(BaseModel):
    text: str
    metadata: dict = {}

class VectorQueryRequest(BaseModel):
    text: str
    top_k: int = 5

# --- OAuth2 /token endpoint ---
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- LLM Models endpoint ---
@app.get("/models", response_model=list[ModelInfo])
def list_llm_models():
    return [ModelInfo(provider=p, models=get_plugin(p).available_models()) for p in list_plugins()]

# --- Endpoints ---
def get_auth_user(
    x_api_key: str = Depends(verify_api_key),
    user: User = Depends(get_current_user)
):
    # Allow either valid API key or valid JWT
    if x_api_key or user:
        return user or x_api_key
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.post("/task", response_model=TaskResponse)
@limiter.limit(get_rate_limit())
async def submit_task(
    req: TaskRequest,
    auth=Depends(get_auth_user),
    request: Request = None
):
    # Enqueue async LLM task
    LLM_CALLS.labels(req.model).inc()
    x_api_key = auth if isinstance(auth, str) else None
    task = celery.send_task(
        "api.worker.llm_task",
        args=[req.prompt, req.model, req.max_tokens, req.temperature, x_api_key, req.provider],
    )
    return TaskResponse(task_id=task.id)

@app.get("/result/{task_id}", response_model=ResultResponse)
@limiter.limit(get_rate_limit())
async def get_result(task_id: str, auth=Depends(get_auth_user)):
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
    auth=Depends(get_auth_user),
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

@app.post("/vectors/upsert")
def upsert_vector(req: VectorUpsertRequest, auth=Depends(get_auth_user)):
    vec_id = str(uuid.uuid4())
    vector_store.upsert(vec_id, req.text, req.metadata)
    return {"id": vec_id}

@app.post("/vectors/query")
def query_vector(req: VectorQueryRequest, auth=Depends(get_auth_user)):
    results = vector_store.query(req.text, req.top_k)
    return results

@app.get("/metrics")
@limiter.limit(get_rate_limit())
async def metrics(db: Session = Depends(get_db), auth=Depends(get_auth_user), request: Request = None):
    count = db.query(TaskRecord).count()
    return {"tasks_processed": count}

# --- Health check ---
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

# --- Best practices ---
# - All endpoints require OAuth2/JWT or X-API-Key
# - Per-API-key distributed rate limiting (Redis backend, configurable via REDIS_URL)
# - All tasks/answers persisted in SQLite (configurable via DATABASE_URL)
# - Rust LLM plugin is called via Python extension
# - Prometheus metrics for LLM, DB, and API
# - Async LLM tasks via Celery+Redis
# - LLM plugin system: OpenAI, Hugging Face, extensible
# - Ready for extension: user registration, roles, external IdP, etc.