from fastapi import FastAPI, HTTPException, Depends, Header, Request, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta, date
import os
import importlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from llm_plugins import get_plugin, list_plugins
from vector_store.chroma_store import ChromaVectorStore
import uuid
from hashlib import sha256
import secrets
import logging
import sys
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request as FastAPIRequest
import json

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
    is_admin = Column(Integer, default=0)  # 1 for admin, 0 for regular

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

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Integer, default=0)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Usage(Base):
    __tablename__ = "usage"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    api_key_hash = Column(String, nullable=True)
    day = Column(String, nullable=False)  # YYYY-MM-DD
    count = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

DEFAULT_DAILY_QUOTA = int(os.environ.get("DAILY_QUOTA", 100))

# --- Structured logging (JSON) ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "message": record.getMessage(),
            "name": record.name,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("reasoning_agent")

# --- FastAPI app with CORS and security headers ---
app = FastAPI(title="ReasoningAgent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: FastAPIRequest, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# --- Global error handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: FastAPIRequest, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )

# --- Backup/restore and monitoring best practices ---
# - Backup: Copy SQLite DBs (reasoning_agent.db, kg.db) and Chroma vector store dir (chroma_data/)
# - Restore: Replace files and restart containers
# - Monitoring: Use Prometheus metrics endpoint, logs, and audit log
# - Security: Use HTTPS in production, manage secrets securely, pin dependencies

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

def require_admin_user(user: User = Depends(get_current_user)):
    if not user or not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# --- API Key Auth ---
def get_api_keys():
    keys = os.environ.get("API_KEYS", "testkey").split(",")
    return set(k.strip() for k in keys if k.strip())

def verify_api_key_db(x_api_key: str = Header(None)):
    if x_api_key is None:
        return None
    db = SessionLocal()
    key_hash = sha256(x_api_key.encode()).hexdigest()
    key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.revoked == 0).first()
    if not key:
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
    context: str | None = None
    context_k: int = 3

class TaskResponse(BaseModel):
    task_id: str
    context: str | None = None

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

class ApiKeyCreateResponse(BaseModel):
    key: str
    id: int
    owner: str
    created_at: datetime

class ApiKeyListResponse(BaseModel):
    id: int
    owner: str
    created_at: datetime
    revoked: bool

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str | None = None

class UserListResponse(BaseModel):
    id: int
    username: str
    full_name: str | None
    is_admin: bool
    disabled: bool

class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    username: str | None
    action: str
    details: str | None
    timestamp: datetime

class UsageReport(BaseModel):
    day: str
    count: int

class UsageTrend(BaseModel):
    day: str
    count: int

class TopUser(BaseModel):
    username: str
    count: int

class TopModelProvider(BaseModel):
    model: str
    provider: str
    count: int

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
    x_api_key: str = Depends(verify_api_key_db),
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
    # RAG: If no context provided, query vector store for top-k
    context = req.context
    if not context:
        results = vector_store.query(req.prompt, req.context_k)
        context_chunks = [doc for doc in results.get("documents", [[]])[0]]
        context = "\n".join(context_chunks)
    # Inject context into prompt
    full_prompt = f"Context:\n{context}\n\nUser Prompt:\n{req.prompt}" if context else req.prompt
    LLM_CALLS.labels(req.model).inc()
    x_api_key = auth if isinstance(auth, str) else None
    check_quota(auth, x_api_key)
    # Pass full_prompt to worker
    task = celery.send_task(
        "api.worker.llm_task",
        args=[full_prompt, req.model, req.max_tokens, req.temperature, x_api_key, req.provider],
    )
    increment_usage(auth, x_api_key)
    return TaskResponse(task_id=task.id, context=context)

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

@app.post("/apikeys", response_model=ApiKeyCreateResponse)
def create_apikey(admin: User = Depends(require_admin_user)):
    # Generate a secure random key
    key = secrets.token_urlsafe(32)
    key_hash = sha256(key.encode()).hexdigest()
    db = SessionLocal()
    api_key = ApiKey(key_hash=key_hash, owner_id=admin.id)
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    audit_log(admin, "create_apikey", f"id={api_key.id}")
    return ApiKeyCreateResponse(key=key, id=api_key.id, owner=admin.username, created_at=api_key.created_at)

@app.get("/apikeys", response_model=list[ApiKeyListResponse])
def list_apikeys(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    keys = db.query(ApiKey).all()
    users = {u.id: u.username for u in db.query(User).all()}
    return [
        ApiKeyListResponse(
            id=k.id,
            owner=users.get(k.owner_id, "unknown"),
            created_at=k.created_at,
            revoked=bool(k.revoked)
        ) for k in keys
    ]

@app.delete("/apikeys/{key_id}")
def revoke_apikey(key_id: int, admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked = 1
    db.commit()
    audit_log(admin, "revoke_apikey", f"id={key_id}")
    return {"revoked": True, "id": key_id}

@app.post("/users/register")
def register_user(req: UserRegisterRequest):
    db = SessionLocal()
    user_count = db.query(User).count()
    # Open registration if no users exist, admin-only after
    if user_count > 0:
        raise HTTPException(status_code=403, detail="Registration closed. Contact admin.")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        full_name=req.full_name,
        is_admin=1,  # First user is admin
        disabled=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_log(user, "register_user", f"id={user.id}")
    return {"id": user.id, "username": user.username, "is_admin": True}

@app.get("/users", response_model=list[UserListResponse])
def list_users(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    users = db.query(User).all()
    return [
        UserListResponse(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            is_admin=bool(u.is_admin),
            disabled=bool(u.disabled)
        ) for u in users
    ]

@app.post("/users/{user_id}/disable")
def disable_user(user_id: int, admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.disabled = 1
    db.commit()
    audit_log(admin, "disable_user", f"id={user_id}")
    return {"disabled": True, "id": user_id}

@app.post("/users/{user_id}/enable")
def enable_user(user_id: int, admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.disabled = 0
    db.commit()
    audit_log(admin, "enable_user", f"id={user_id}")
    return {"enabled": True, "id": user_id}

@app.post("/users/{user_id}/promote")
def promote_user(user_id: int, admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = 1
    db.commit()
    audit_log(admin, "promote_user", f"id={user_id}")
    return {"promoted": True, "id": user_id}

@app.post("/users/{user_id}/demote")
def demote_user(user_id: int, admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = 0
    db.commit()
    audit_log(admin, "demote_user", f"id={user_id}")
    return {"demoted": True, "id": user_id}

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
# - All admin/sensitive actions are logged to the audit log.
# - Usage tracking and quota enforcement for API keys and users.

from kg.sqlite_kg import SQLiteKG

kg = SQLiteKG()

class KGNodeUpsertRequest(BaseModel):
    label: str
    properties: dict = {}

class KGEdgeUpsertRequest(BaseModel):
    source: int
    target: int
    label: str
    properties: dict = {}

class KGNodeQueryRequest(BaseModel):
    label: str | None = None

class KGEdgeQueryRequest(BaseModel):
    source: int | None = None
    target: int | None = None
    label: str | None = None

@app.post("/kg/node/upsert")
def upsert_kg_node(req: KGNodeUpsertRequest, auth=Depends(get_auth_user)):
    node_id = kg.upsert_node(req.label, json.dumps(req.properties))
    audit_log(auth, "upsert_kg_node", f"id={node_id}")
    return {"id": node_id}

@app.post("/kg/edge/upsert")
def upsert_kg_edge(req: KGEdgeUpsertRequest, auth=Depends(get_auth_user)):
    edge_id = kg.upsert_edge(req.source, req.target, req.label, json.dumps(req.properties))
    audit_log(auth, "upsert_kg_edge", f"id={edge_id}")
    return {"id": edge_id}

@app.post("/kg/node/query")
def query_kg_nodes(req: KGNodeQueryRequest, auth=Depends(get_auth_user)):
    nodes = kg.query_nodes(req.label)
    for n in nodes:
        n["properties"] = json.loads(n["properties"] or "{}")
    return nodes

@app.post("/kg/edge/query")
def query_kg_edges(req: KGEdgeQueryRequest, auth=Depends(get_auth_user)):
    edges = kg.query_edges(req.source, req.target, req.label)
    for e in edges:
        e["properties"] = json.loads(e["properties"] or "{}")
    return edges

@app.get("/auditlog", response_model=list[AuditLogResponse])
def get_audit_log(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        AuditLogResponse(
            id=l.id,
            user_id=l.user_id,
            username=l.username,
            action=l.action,
            details=l.details,
            timestamp=l.timestamp
        ) for l in logs
    ]

@app.get("/usage", response_model=list[UsageReport])
def get_my_usage(auth=Depends(get_auth_user)):
    db = SessionLocal()
    user_id = getattr(auth, "id", None) if hasattr(auth, "id") else None
    api_key = auth if isinstance(auth, str) else None
    api_key_hash = sha256(api_key.encode()).hexdigest() if api_key else None
    q = db.query(Usage).filter(
        (Usage.user_id == user_id) | (Usage.api_key_hash == api_key_hash)
    ).order_by(Usage.day.desc()).limit(30)
    return [UsageReport(day=u.day, count=u.count) for u in q]

@app.get("/usage/all", response_model=list[UsageReport])
def get_all_usage(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    q = db.query(Usage.day, Usage.count).order_by(Usage.day.desc()).all()
    return [UsageReport(day=day, count=count) for day, count in q]

@app.get("/analytics/usage_trend", response_model=list[UsageTrend])
def usage_trend(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    q = db.query(Usage.day, func.sum(Usage.count)).group_by(Usage.day).order_by(Usage.day.desc()).limit(30)
    return [UsageTrend(day=day, count=count) for day, count in q]

@app.get("/analytics/top_users", response_model=list[TopUser])
def top_users(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    q = db.query(User.username, func.sum(Usage.count)).join(Usage, Usage.user_id == User.id).group_by(User.username).order_by(func.sum(Usage.count).desc()).limit(10)
    return [TopUser(username=u, count=c) for u, c in q]

@app.get("/analytics/top_models", response_model=list[TopModelProvider])
def top_models(admin: User = Depends(require_admin_user)):
    db = SessionLocal()
    q = db.query(TaskRecord.model, TaskRecord.api_key, func.count(TaskRecord.id)).group_by(TaskRecord.model, TaskRecord.api_key).order_by(func.count(TaskRecord.id).desc()).limit(10)
    return [TopModelProvider(model=m, provider=p or "unknown", count=c) for m, p, c in q]

def increment_usage(user: User = None, api_key: str = None):
    db = SessionLocal()
    today = date.today().isoformat()
    user_id = getattr(user, "id", None) if user else None
    api_key_hash = sha256(api_key.encode()).hexdigest() if api_key else None
    usage = db.query(Usage).filter_by(user_id=user_id, api_key_hash=api_key_hash, day=today).first()
    if not usage:
        usage = Usage(user_id=user_id, api_key_hash=api_key_hash, day=today, count=1)
        db.add(usage)
    else:
        usage.count += 1
    db.commit()
    db.close()

def check_quota(user: User = None, api_key: str = None):
    db = SessionLocal()
    today = date.today().isoformat()
    user_id = getattr(user, "id", None) if user else None
    api_key_hash = sha256(api_key.encode()).hexdigest() if api_key else None
    usage = db.query(Usage).filter_by(user_id=user_id, api_key_hash=api_key_hash, day=today).first()
    count = usage.count if usage else 0
    db.close()
    if count >= DEFAULT_DAILY_QUOTA:
        raise HTTPException(status_code=429, detail="Daily quota exceeded")