# AI Gym App (prototype)

A workout-tracking prototype with a FastAPI backend and a SwiftUI iOS companion app.

## Structure

- `backend/` - FastAPI + SQLModel (SQLite). Routers for `exercises`, `onboarding`, `workouts` and `companion`;
  the exercise library is seeded from `app/seed/exercises.csv` / `.json`.
- `companion-ios/SwiftUI-Companion/` - SwiftUI app skeleton (workout view, set rows, API service).
- `docs/` - onboarding schema (`onboarding-schema.json`) and wireframes (`wireframes.mmd`).
- Onboarding and register screen mockups are the `.svg` files in this folder.

## Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for the interactive API docs.

## Status

Early prototype: no authentication or tests yet, and dependency versions are pinned to 2023-era releases.
