from fastapi import Header, HTTPException, Depends, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from typing import Optional

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing (for demo, one user)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
FAKE_USER = {
    "username": "admin",
    "hashed_password": pwd_context.hash("adminpass"),
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str):
    if username == FAKE_USER["username"] and verify_password(password, FAKE_USER["hashed_password"]):
        return FAKE_USER
    return None

def create_access_token(data: dict):
    from datetime import datetime, timedelta
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), x_api_key: str = Header(None)):
    api_key = os.getenv("API_KEY", "your-secret-key")
    if x_api_key and x_api_key == api_key:
        return {"username": "api_key_user"}
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return {"username": username}
    except JWTError:
        raise credentials_exception