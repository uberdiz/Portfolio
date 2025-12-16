from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import date, datetime

class Exercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    primary_muscles: Optional[str] = None   # comma separated
    secondary_muscles: Optional[str] = None
    equipment: Optional[str] = None        # comma separated
    rep_range: Optional[str] = None
    cues: Optional[str] = None
    demo_url: Optional[str] = None

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    level: Optional[str] = None  # beginner/intermediate/advanced
    equipment: Optional[str] = None
    weekly_goal: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Workout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    date: date
    completed: bool = False

class WorkoutExercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id")
    exercise_id: int = Field(foreign_key="exercise.id")
    sets: int = 3
    reps: int = 8
    target_weight: Optional[float] = None

class SetLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_exercise_id: int = Field(foreign_key="workoutexercise.id")
    set_number: int
    reps_done: int
    weight: Optional[float] = None
    rir: Optional[int] = None
    rpe: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Progression(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    exercise_id: int = Field(foreign_key="exercise.id")
    last_weight: Optional[float] = None
    failures: int = 0
    last_trained: Optional[datetime] = None
