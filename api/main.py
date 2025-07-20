from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from api.schemas import TaskRequest, TaskResult
from api.auth import get_current_user, authenticate_user, create_access_token
from uuid import uuid4
import os
from prometheus_fastapi_instrumentator import Instrumentator
from agent.plugin_loader import load_plugins
from agent.logging_config import logger
from celery.result import AsyncResult
from celery_worker import process_task_celery, celery_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import traceback

# OpenTelemetry tracing
if os.getenv("OTEL_ENABLED", "0") == "1":
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    trace.set_tracer_provider(TracerProvider())
    span_processor = BatchSpanProcessor(OTLPSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Instrumentator().instrument(app).expose(app)

# --- Global error handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail} | Path: {request.url}")
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.status_code, "message": exc.detail}})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"ValidationError: {exc.errors()} | Path: {request.url}")
    return JSONResponse(status_code=422, content={"error": {"code": 422, "message": "Validation error", "details": exc.errors()}})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc} | Path: {request.url}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"error": {"code": 500, "message": "Internal server error"}})

if os.getenv("OTEL_ENABLED", "0") == "1":
    FastAPIInstrumentor.instrument_app(app)

tasks = {}
ws_connections = {}

llm, kg, vector_store, metrics, prompt_builder = load_plugins()

# OAuth2 token endpoint
from fastapi.security import OAuth2PasswordRequestForm
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks", response_model=TaskResult)
@limiter.limit("5/minute")
async def submit_task(request: Request, task: TaskRequest, user=Depends(get_current_user)):
    task_id = str(uuid4())
    tasks[task_id] = {"status": "pending", "result": None, "celery_id": None}
    celery_result = process_task_celery.apply_async(args=[task_id, task.input])
    tasks[task_id]["celery_id"] = celery_result.id
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.get("/tasks/{task_id}", response_model=TaskResult)
@limiter.limit("20/minute")
async def get_task(request: Request, task_id: str, user=Depends(get_current_user)):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    celery_id = tasks[task_id]["celery_id"]
    result = AsyncResult(celery_id, app=celery_app)
    if result.ready():
        try:
            output = result.get()
            if output.get("status") == "failed":
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["result"] = output["result"]
            else:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = output["result"]
        except Exception as e:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["result"] = str(e)
    return TaskResult(id=task_id, status=tasks[task_id]["status"], result=tasks[task_id]["result"])

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    await websocket.accept()
    ws_connections.setdefault(task_id, []).append(websocket)
    try:
        # Send initial status
        if task_id in tasks:
            await websocket.send_json({"status": tasks[task_id]["status"], "result": tasks[task_id]["result"]})
        celery_id = tasks[task_id]["celery_id"]
        result = AsyncResult(celery_id, app=celery_app)
        while not result.ready():
            try:
                await websocket.receive_text()  # Keep connection open
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                await websocket.send_json({"error": f"WebSocket error: {str(e)}"})
                await websocket.close()
                return
        try:
            output = result.get()
            if output.get("status") == "failed":
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["result"] = output["result"]
                await websocket.send_json({"status": "failed", "result": output["result"]})
            else:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = output["result"]
                await websocket.send_json({"status": "completed", "result": output["result"]})
        except Exception as e:
            logger.error(f"WebSocket result error: {e}")
            await websocket.send_json({"error": f"Result error: {str(e)}"})
            await websocket.close()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
        ws_connections[task_id].remove(websocket)