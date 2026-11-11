"""Load repeatable local demo data. Run from backend: .venv/bin/python seed.py."""
from pathlib import Path

import psycopg

from app.config import settings


def main():
    with psycopg.connect(settings.database_url) as conn:
        with conn.transaction():
            conn.execute(Path(__file__).with_name("seed.sql").read_text())
        counts = conn.execute(
            "SELECT (SELECT count(*) FROM users), "
            "(SELECT count(*) FROM penpalships), (SELECT count(*) FROM letters)"
        ).fetchone()
        print(f"Demo ready: {counts[0]} users, {counts[1]} pen-palships, {counts[2]} letters")


if __name__ == "__main__":
    main()
