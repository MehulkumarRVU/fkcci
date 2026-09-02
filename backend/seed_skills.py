from app.database import SessionLocal
from app.seed_data import seed_default_skills_if_empty

if __name__ == '__main__':
    with SessionLocal() as db:
        result = seed_default_skills_if_empty(db)
        print(result)
