from fastapi import APIRouter, Depends, HTTPException
from app.db import get_session
from sqlmodel import Session
from app import crud

router = APIRouter(prefix="/companion", tags=["companion"])

@router.get("/current_workout/{user_id}")
def current_workout(user_id: int, session: Session = Depends(get_session)):
    # find today's workout
    from datetime import date
    w = session.exec(__import__("sqlmodel").select(__import__("app.models", fromlist=["models"]).models.Workout).where(__import__("app.models", fromlist=["models"]).models.Workout.user_id==user_id, __import__("app.models", fromlist=["models"]).models.Workout.date==date.today())).first()
    if not w:
        return {"message": "no workout today"}
    # list exercises
    wes = session.exec(__import__("sqlmodel").select(__import__("app.models", fromlist=["models"]).models.WorkoutExercise).where(__import__("app.models", fromlist=["models"]).models.WorkoutExercise.workout_id==w.id)).all()
    data = []
    for we in wes:
        ex = session.get(__import__("app.models", fromlist=["models"]).models.Exercise, we.exercise_id)
        data.append({
            "workout_exercise_id": we.id,
            "exercise_id": ex.id,
            "name": ex.name,
            "sets": we.sets,
            "reps": we.reps,
            "target_weight": we.target_weight,
            "cues": ex.cues,
            "demo_url": ex.demo_url
        })
    return {"workout": {"id": w.id, "exercises": data}}
