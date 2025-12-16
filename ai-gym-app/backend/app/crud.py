from sqlmodel import select
from app import models
from sqlmodel import Session
from app.db import engine
from datetime import date, datetime, timedelta

def list_exercises(session: Session):
    return session.exec(select(models.Exercise)).all()

def get_exercise(session: Session, exercise_id: int):
    return session.get(models.Exercise, exercise_id)

def seed_exercises(session: Session, exercises: list[dict]):
    for e in exercises:
        ex = models.Exercise(**e)
        session.add(ex)
    session.commit()

def create_user(session: Session, email: str, level: str, equipment: str, weekly_goal: int):
    u = models.User(email=email, level=level, equipment=equipment, weekly_goal=weekly_goal)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u

def create_workout(session: Session, user_id: int, date: date):
    w = models.Workout(user_id=user_id, date=date, completed=False)
    session.add(w)
    session.commit()
    session.refresh(w)
    return w

def add_workout_exercise(session: Session, workout_id: int, exercise_id: int, sets:int=3, reps:int=8, target_weight:float=None):
    we = models.WorkoutExercise(workout_id=workout_id, exercise_id=exercise_id, sets=sets, reps=reps, target_weight=target_weight)
    session.add(we)
    session.commit()
    session.refresh(we)
    return we

def log_set(session: Session, workout_exercise_id:int, set_number:int, reps_done:int, weight:float=None, rir:int=None, rpe:float=None):
    s = models.SetLog(workout_exercise_id=workout_exercise_id, set_number=set_number, reps_done=reps_done, weight=weight, rir=rir, rpe=rpe)
    session.add(s)
    session.commit()
    session.refresh(s)
    return s

def update_progression(session: Session, user_id:int, exercise_id:int, last_weight:float, success:bool):
    q = session.exec(select(models.Progression).where(models.Progression.user_id==user_id, models.Progression.exercise_id==exercise_id)).first()
    if not q:
        q = models.Progression(user_id=user_id, exercise_id=exercise_id, last_weight=last_weight, failures=0, last_trained=datetime.utcnow())
        session.add(q)
    else:
        q.last_trained = datetime.utcnow()
        if success:
            q.last_weight = last_weight
            q.failures = 0
        else:
            q.failures = (q.failures or 0) + 1
            if q.failures >= 2:
                q.last_weight = max(0, (q.last_weight or last_weight) - 10)
    session.commit()
    session.refresh(q)
    return q

def compute_weekly_streak(session: Session, user_id:int, weeks_lookback:int=12):
    # Count how many weeks in a row meet weekly_goal
    user = session.get(models.User, user_id)
    if not user:
        return 0
    today = date.today()
    start = today - timedelta(weeks=weeks_lookback)
    workouts = session.exec(select(models.Workout).where(models.Workout.user_id==user_id, models.Workout.date >= start)).all()
    # group workouts by ISO week
    weeks = {}
    for w in workouts:
        wk = w.date.isocalendar()[1]
        weeks.setdefault(wk, 0)
        if w.completed:
            weeks[wk] += 1
    # compute consecutive weeks up to current week
    streak = 0
    current_week = today.isocalendar()[1]
    for i in range(weeks_lookback):
        wk = current_week - i
        if weeks.get(wk, 0) >= (user.weekly_goal or 0):
            streak += 1
        else:
            break
    return streak
