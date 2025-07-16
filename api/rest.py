from fastapi import FastAPI, Depends, HTTPException, Header, Body
from storage.base import get_storage_backend
import yaml

with open('config.yaml') as f:
    config = yaml.safe_load(f)

storage = get_storage_backend(config['storage'])

app = FastAPI()

def check_auth(authorization: str = Header(...)):
    if authorization != f"Bearer {config['api']['auth_token']}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/data", dependencies=[Depends(check_auth)])
def get_data():
    return storage.load()

@app.post("/data", dependencies=[Depends(check_auth)])
def add_data(item: dict):
    storage.save(item)
    return {"status": "saved"}

@app.post("/vector_search", dependencies=[Depends(check_auth)])
def vector_search(query: dict = Body(...)):
    vector = query.get('vector')
    k = query.get('k', 5)
    if hasattr(storage, 'search'):
        results = storage.search(vector, k)
        return {"results": results}
    return {"error": "Vector search not supported by current storage backend."}