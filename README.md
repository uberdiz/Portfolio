# Early Prototypes

Two early prototypes from late 2025, kept as a record of how my work progressed toward my current projects.
Parts of these prototypes were built with AI coding assistance, and they are not finished products.

My current main projects:

- **[SAINT](https://github.com/uberdiz/SAINT)** - a local, voice-first AI assistant for Windows
- **[AIDE](https://github.com/uberdiz/AIDE)** - an AI-assisted coding environment built on VS Code
- **Live portfolio:** https://sebastianai.vercel.app

## [`ai-dev-ide`](ai-dev-ide/) - AI Dev IDE (Python, Tkinter)

A desktop, multi-agent coding assistant: a planner, coder, tester, fixer and summarizer agent work on a project, with
a file tree, editor tabs, output panels and an optional GitHub step (via PyGithub/GitPython).

```bash
cd ai-dev-ide
pip install -r requirements.txt
python launcher.py
```

You will need to configure an LLM provider in the settings window (see `setup_free_apis.py` for free options).

## [`ai-gym-app`](ai-gym-app/) - AI Gym App (FastAPI + SwiftUI)

A workout-tracking prototype:

- **Backend** (`backend/`): FastAPI + SQLModel (SQLite) with routers for exercises, onboarding, workouts and a
  companion endpoint, seeded from an exercise CSV/JSON.
- **iOS companion** (`companion-ios/`): a SwiftUI app skeleton that talks to the API.

```bash
cd ai-gym-app/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Status

Prototype quality. No tests, and the dependency versions are pinned to 2023-era releases.

## Author

Sebastian Langdon - Information Technology student, Essex North Shore Agricultural & Technical School (Class of 2027)
- sebastian.r.langdon@gmail.com
