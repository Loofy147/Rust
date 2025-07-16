from fastapi import FastAPI, Depends, HTTPException, Header
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