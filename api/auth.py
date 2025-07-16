from fastapi import Header, HTTPException
import os

def verify_api_key(x_api_key: str = Header(...)):
    api_key = os.getenv("API_KEY", "your-secret-key")
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")