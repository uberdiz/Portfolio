from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db import get_session
from app import crud

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post("/create_user")
def create_user(payload: dict, session: Session = Depends(get_session)):
    # payload: {email, level, equipment (comma), weekly_goal}
    if not payload.get("email"):
        raise HTTPException(status_code=400, detail="email required")
    user = crud.create_user(session, payload["email"], payload.get("level"), payload.get("equipment"), payload.get("weekly_goal", 3))
    return {"user_id": user.id}
