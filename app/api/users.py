from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

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

# --- Endpoints ---
@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate):
    # TODO: Implement user creation logic
    # Example response (stub)
    return UserOut(id="uuid", email=user.email, name=user.name, org_id=user.org_id, role="user")

@router.post("/login")
def login_user(email: EmailStr, password: str):
    # TODO: Implement authentication logic
    return {"access_token": "fake-token", "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_profile():
    # TODO: Implement user profile retrieval (use auth)
    return UserOut(id="uuid", email="user@example.com", name="User", org_id="org", role="user")

@router.get("/", response_model=List[UserOut])
def list_users():
    # TODO: Implement user listing (admin only)
    return [UserOut(id="uuid", email="user@example.com", name="User", org_id="org", role="user")]