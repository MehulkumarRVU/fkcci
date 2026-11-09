from pathlib import Path
from sqlalchemy import text
from .database import engine


def apply_migrations():
    if engine.dialect.name != "sqlite":
        raise RuntimeError(
            "The numbered SQL files are legacy SQLite migrations; "
            "PostgreSQL upgrades use init_database compatibility migrations."
        )

    project_root = Path(__file__).resolve().parents[1]
    migrations_dir = project_root / "migrations"
    migrations = sorted(migrations_dir.glob("*.sql"))

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS applied_migrations (
                    id INTEGER PRIMARY KEY,
                    filename TEXT UNIQUE,
                    applied_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
                )
                """
            )
        )

        for m in migrations:
            name = m.name
            exists = conn.execute(text("SELECT 1 FROM applied_migrations WHERE filename = :fn"), {"fn": name}).fetchone()
            if exists:
                continue

            sql = m.read_text(encoding="utf-8")
            # Split into individual statements and execute
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            for stmt in statements:
                conn.execute(text(stmt))

            # Record it as applied
            conn.execute(text("INSERT INTO applied_migrations (filename) VALUES (:fn)"), {"fn": name})


if __name__ == "__main__":
    apply_migrations()
    print("Migrations applied")
