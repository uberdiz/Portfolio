import csv
import json
from pathlib import Path
from sqlmodel import Session
from app.db import init_db, engine
from app import crud
from app.models import Exercise
from app.db import get_session

BASE = Path(__file__).resolve().parent

def csv_to_json(csv_path, json_path):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize keys: fill missing
            row = {
                "name": r.get("name","").strip(),
                "description": r.get("description","").strip(),
                "primary_muscles": r.get("primary_muscles","").strip(),
                "secondary_muscles": r.get("secondary_muscles","").strip(),
                "equipment": r.get("equipment","").strip(),
                "rep_range": r.get("rep_range","").strip(),
                "cues": r.get("cues","").strip(),
                "demo_url": r.get("demo_url","").strip(),
            }
            rows.append(row)
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(rows, jf, indent=2)
    return rows

def seed_db(json_rows):
    init_db()
    with Session(engine) as session:
        # Clear existing
        session.exec("DELETE FROM exercise")
        session.commit()
        for r in json_rows:
            ex = Exercise(**r)
            session.add(ex)
        session.commit()

if __name__ == "__main__":
    csvp = BASE / "exercises.csv"
    jsonp = BASE / "exercises.json"
    rows = csv_to_json(csvp, jsonp)
    print(f"Wrote {len(rows)} exercises to {jsonp}")
    seed_db(rows)
    print("Seeded DB: backend/app/ai_gym.db")
