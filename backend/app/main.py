"""
FastAPI application entrypoint.

The lifespan context opens the psycopg ConnectionPool once when the app
starts and closes it cleanly when the app shuts down, so every request
during the app's lifetime reuses pooled connections instead of opening a
new one each time.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import pool
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    pool.wait()
    yield
    pool.close()


app = FastAPI(title="CS348 Project API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
