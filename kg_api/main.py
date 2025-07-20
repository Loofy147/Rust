import os
import logging
import asyncio
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from typing import Optional, Dict, Any
from kg_engine_async import AsyncKnowledgeGraphEngine, EntityType, RelationshipType, Entity, Relationship
from kg_api.auth import get_current_user, authenticate_user, create_access_token

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
Instrumentator().instrument(app).expose(app)

kg = AsyncKnowledgeGraphEngine()

class EntityIn(BaseModel):
    type: EntityType
    name: str
    properties: Dict[str, Any] = {}

class RelationshipIn(BaseModel):
    source_id: str
    target_id: str
    type: RelationshipType
    weight: float = 1.0
    confidence: float = 0.8
    context: Dict[str, Any] = {}

@app.post('/token')
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/entities')
@limiter.limit("10/minute")
async def add_entity(entity: EntityIn, user=Depends(get_current_user)):
    ent = Entity(id='', type=entity.type, name=entity.name, properties=entity.properties)
    eid = await kg.add_entity(ent)
    return {"id": eid}

@app.get('/entities/{entity_id}')
@limiter.limit("30/minute")
async def get_entity(entity_id: str, user=Depends(get_current_user)):
    ent = await kg.get_entity(entity_id)
    if not ent:
        raise HTTPException(404, "Entity not found")
    return ent

@app.post('/relationships')
@limiter.limit("10/minute")
async def add_relationship(rel: RelationshipIn, user=Depends(get_current_user)):
    relationship = Relationship(id='', **rel.dict())
    rid = await kg.add_relationship(relationship)
    return {"id": rid}

@app.get('/relationships/{rel_id}')
@limiter.limit("30/minute")
async def get_relationship(rel_id: str, user=Depends(get_current_user)):
    rel = await kg.get_relationship(rel_id)
    if not rel:
        raise HTTPException(404, "Relationship not found")
    return rel

@app.get('/entities')
@limiter.limit("30/minute")
async def query_entities(type: Optional[EntityType] = None, name: Optional[str] = None, user=Depends(get_current_user)):
    results = await kg.query_entities(entity_type=type, name_pattern=name)
    return results

@app.get('/reasoning')
@limiter.limit("10/minute")
async def reasoning(query: str, user=Depends(get_current_user)):
    # Example: pass query to engine's reasoning method
    result = await kg.execute_reasoning(query)
    return result

@app.get('/health', tags=["Admin"])
async def health():
    return {"status": "ok"}

@app.get('/version', tags=["Admin"])
async def version():
    return {"version": "1.0.0"}

@app.get('/stats', tags=["Admin"])
async def stats():
    return {
        "entity_count": len(kg.entities),
        "relationship_count": len(kg.relationships)
    }

@app.post('/admin/reload', tags=["Admin"])
async def admin_reload(user=Depends(get_current_user)):
    if user["username"] != "admin":
        raise HTTPException(403, "Admin only")
    # Placeholder: reload rules/listeners
    await kg.reload_rules_and_listeners()
    return {"status": "reloaded"}

@app.get('/export', tags=["Admin"])
async def export_graph(user=Depends(get_current_user)):
    if user["username"] != "admin":
        raise HTTPException(403, "Admin only")
    # Placeholder: export as JSON
    return {"entities": [e.__dict__ for e in kg.entities.values()], "relationships": [r.__dict__ for r in kg.relationships.values()]}

@app.post('/import', tags=["Admin"])
async def import_graph(data: Dict[str, Any], user=Depends(get_current_user)):
    if user["username"] != "admin":
        raise HTTPException(403, "Admin only")
    # Placeholder: import entities/relationships
    return {"status": "imported"}

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled Exception: {exc}")
    return JSONResponse(status_code=500, content={"error": {"code": 500, "message": str(exc)}})