from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.organization import Organization
import uuid
from datetime import datetime

router = APIRouter(prefix="/orgs", tags=["organizations"])

class OrgCreate(BaseModel):
    name: str

class OrgOut(BaseModel):
    id: str
    name: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=OrgOut)
def create_org(org: OrgCreate, db: Session = Depends(get_db)):
    if db.query(Organization).filter(Organization.name == org.name).first():
        raise HTTPException(status_code=400, detail="Organization already exists")
    db_org = Organization(id=uuid.uuid4(), name=org.name, created_at=datetime.utcnow())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return OrgOut(id=str(db_org.id), name=db_org.name)

@router.get("/", response_model=List[OrgOut])
def list_orgs(db: Session = Depends(get_db)):
    orgs = db.query(Organization).all()
    return [OrgOut(id=str(o.id), name=o.name) for o in orgs]

@router.get("/{org_id}", response_model=OrgOut)
def get_org(org_id: str, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrgOut(id=str(org.id), name=org.name)