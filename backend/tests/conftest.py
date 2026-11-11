"""Tests use real PostgreSQL in a disposable schema, preserving demo data."""

from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql

from app.config import settings
from app.db import get_conn
from app.main import app


@pytest.fixture
def db():
    schema = "envoi_test_" + uuid4().hex
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            migration = Path(__file__).parents[1] / "migrations/001_stage_two.sql"
            with conn.transaction():
                conn.execute(migration.read_text())
            yield conn
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def people(db):
    ids = []
    for name in ("Ada", "Bea", "Cal", "Dee"):
        ids.append(
            db.execute(
                "INSERT INTO users(username,email,display_name) VALUES (%s,%s,%s) RETURNING id",
                (name.lower(), name.lower() + "@example.test", name),
            ).fetchone()[0]
        )
    return ids


@pytest.fixture
def pair(db, people):
    return db.execute(
        "INSERT INTO penpalships(user_a_id,user_b_id) VALUES (%s,%s) RETURNING id",
        (people[0], people[1]),
    ).fetchone()[0]


@pytest.fixture
def client(db):
    def test_connection():
        yield db

    app.dependency_overrides[get_conn] = test_connection
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
