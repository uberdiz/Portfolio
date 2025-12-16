from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db import get_session
from app import crud, models

router = APIRouter(prefix="/exercises", tags=["exercises"])

@router.get("/")
def list_exercises(session: Session = Depends(get_session)):
    return crud.list_exercises(session)

@router.get("/{exercise_id}")
def get_exercise(exercise_id: int, session: Session = Depends(get_session)):
    return crud.get_exercise(session, exercise_id)
