import jwt
import os
import datetime
from fastapi import HTTPException

JWT_SECRET = os.environ.get('JWT_SECRET', 'changemejwtsecret')
JWT_ALGO = 'HS256'
JWT_EXP_MINUTES = 60

# Demo user store (replace with DB in production)
USERS = {
    "admin": {"password": "adminpass", "tenant": "default"},
    "user1": {"password": "user1pass", "tenant": "tenant1"}
}

def create_token(username, tenant):
    payload = {
        "sub": username,
        "tenant": tenant,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def authenticate_user(username, password):
    user = USERS.get(username)
    if user and user["password"] == password:
        return user
    return None