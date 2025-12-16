from fastapi import APIRouter, Depends, HTTPException
from app.db import get_session
from sqlmodel import Session
from app import crud
from datetime import date
from random import sample

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("/create")
def create_workout(payload: dict, session: Session = Depends(get_session)):
    # payload: {user_id, date (YYYY-MM-DD) optional}
    d = payload.get("date")
    if d:
        d = date.fromisoformat(d)
    else:
        d = date.today()
    w = crud.create_workout(session, payload["user_id"], d)
    # simple plan: pick 4 exercises from user's equipment
    user = session.get(__import__("app.models", fromlist=["models"]).models.User, payload["user_id"])
    exs = session.exec(__import__("sqlmodel").select(__import__("app.models", fromlist=["models"]).models.Exercise)).all()
    # filter by equipment if set
    if user and user.equipment:
        allowed = [e for e in exs if any(eq.strip().lower() in (user.equipment or "").lower() for eq in (e.equipment or "").split(","))]
        if len(allowed) < 4:
            allowed = exs
    else:
        allowed = exs
    chosen = sample(allowed, min(len(allowed), 4))
    for e in chosen:
        crud.add_workout_exercise(session, w.id, e.id, sets=3, reps=8)
    return {"workout_id": w.id}

@router.post("/log_set")
def log_set(payload: dict, session: Session = Depends(get_session)):
    # payload: {workout_exercise_id, set_number, reps_done, weight, rir, rpe}
    s = crud.log_set(session, payload["workout_exercise_id"], payload["set_number"], payload["reps_done"], payload.get("weight"), payload.get("rir"), payload.get("rpe"))
    # update progression: success if reps_done >= target reps (crud reads we)
    we = session.get(__import__("app.models", fromlist=["models"]).models.WorkoutExercise, payload["workout_exercise_id"])
    success = payload["reps_done"] >= (we.reps or 0)
    # find user via workout
    workout = session.get(__import__("app.models", fromlist=["models"]).models.Workout, we.workout_id)
    crud.update_progression(session, workout.user_id, we.exercise_id, payload.get("weight") or 0, success)
    return {"set_id": s.id}
