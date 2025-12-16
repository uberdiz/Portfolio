from fastapi import FastAPI
from app.db import init_db
from app.routers import exercises, onboarding, workouts, companion

app = FastAPI(title="AI Gym App - Backend (SQLite)")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(exercises.router)
app.include_router(onboarding.router)
app.include_router(workouts.router)
app.include_router(companion.router)
