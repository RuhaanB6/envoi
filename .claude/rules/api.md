---
paths: ["backend/app/**/*.py"]
---

# API conventions

- One router module per resource in `app/routers/`, each exposing `router =
  APIRouter()`, mounted in `app/main.py` with `prefix="/api"` and a tag.
  Paths inside the module are relative (`@router.get("/health")`).
- Connections come from the dependency, never from module-level state:
  `def handler(conn: Connection = Depends(get_conn))`. See `app/routers/health.py`
  for the canonical shape.
- Pydantic models live beside the router that uses them: `LetterCreate` /
  `LetterUpdate` for request bodies, `LetterOut` for responses. Declare the
  `response_model` so the shape is enforced, and never return raw DB rows.
- Rows come back as tuples by default; use an explicit row factory or index
  positionally — do not assume dict access.
- Errors: raise `HTTPException(status_code, detail="...")`. `detail` is a plain
  human sentence. FastAPI's `{"detail": ...}` body is the only error shape;
  do not invent an envelope.
- A rule the database already enforces (a procedure raising on an edit after
  delivery) is caught and translated to a 4xx here — it is not re-implemented
  in Python.
- Auth is a dependency (`current_user`) that reads the httpOnly session cookie,
  hashes it and looks up `sessions`. Protected routes take it via `Depends`;
  never parse the cookie inline in a handler.
- Settings are read from `app.config.settings`, never `os.environ` directly.
- Ruff runs with `select = ["E", "F", "B"]` at line-length 100.
