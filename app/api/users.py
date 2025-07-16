from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.organization import Organization
from passlib.context import CryptContext
import uuid
from jose import jwt
from app.config import settings
from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["users"])

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- JWT ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    org_id: str

class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str
    org_id: str
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Utils ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- Endpoints ---
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        id=uuid.uuid4(),
        email=user.email,
        password_hash=get_password_hash(user.password),
        name=user.name,
        org_id=user.org_id,
        role="user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserOut(
        id=str(db_user.id),
        email=db_user.email,
        name=db_user.name,
        org_id=str(db_user.org_id),
        role=db_user.role,
    )

@router.post("/login", response_model=Token)
def login_user(email: EmailStr, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_profile(db: Session = Depends(get_db)):
    # TODO: Use authentication to get current user
    user = db.query(User).first()  # Stub: get first user
    return UserOut(
        id=str(user.id),
        email=user.email,
        name=user.name,
        org_id=str(user.org_id),
        role=user.role,
    )

@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [UserOut(
        id=str(u.id),
        email=u.email,
        name=u.name,
        org_id=str(u.org_id),
        role=u.role,
    ) for u in users]