"""Local demo identities, draft CRUD, and a filterable SQL mailbox report.

Demo user selection is deliberately not authentication. Run locally only.
"""

from datetime import date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from psycopg import Connection, IntegrityError
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db import get_conn
from app.queries import CREATE_LETTER, DELETE_LETTER, MAILBOX_REPORT, UPDATE_LETTER

router = APIRouter()
Db = Annotated[Connection, Depends(get_conn)]
Mode = Literal["direct", "penpal"]
Status = Literal["draft", "in_transit", "delivered"]


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str


class PenpalshipOut(BaseModel):
    id: int
    correspondent_id: int
    correspondent_name: str
    status: str


class OptionsOut(BaseModel):
    recipients: list[UserOut]
    penpalships: list[PenpalshipOut]
    correspondents: list[UserOut]
    modes: list[str]
    statuses: list[str]


class LetterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient_id: int = Field(gt=0)
    penpalship_id: int | None = Field(default=None, gt=0)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=50000)
    mode: Mode

    @field_validator("subject", "body")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Please enter some text.")
        return value


class LetterOut(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    penpalship_id: int | None
    subject: str
    body: str
    mode: Mode
    status: Status
    created_at: datetime
    updated_at: datetime
    send_at: datetime | None
    deliver_at: datetime | None
    delivered_at: datetime | None
    sender_name: str
    recipient_name: str
    word_count: int
    is_sent: bool
    can_edit: bool


class ReportOut(BaseModel):
    matching_count: int
    average_word_count: float
    sent_count: int
    received_count: int
    letters: list[LetterOut]


class WriteOut(BaseModel):
    id: int


def demo_user(conn: Db, user_id: int = Query(gt=0)) -> int:
    if not conn.execute("SELECT id FROM users WHERE id = %s", (user_id,)).fetchone():
        raise HTTPException(404, "Demo user not found.")
    return user_id


Identity = Annotated[int, Depends(demo_user)]


@router.get("/users", response_model=list[UserOut])
def users(conn: Db):
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "SELECT id, username, display_name FROM users ORDER BY display_name, id"
        ).fetchall()


@router.get("/options", response_model=OptionsOut)
def options(conn: Db, user_id: Identity):
    with conn.cursor(row_factory=dict_row) as cur:
        recipients = cur.execute(
            "SELECT id, username, display_name FROM users WHERE id <> %s ORDER BY display_name, id",
            (user_id,),
        ).fetchall()
        pairs = cur.execute(
            "SELECT p.id, u.id AS correspondent_id, u.display_name AS correspondent_name, "
            "p.status FROM penpalships p JOIN users u ON u.id = "
            "CASE WHEN p.user_a_id = %s THEN p.user_b_id ELSE p.user_a_id END "
            "WHERE (p.user_a_id = %s OR p.user_b_id = %s) AND p.status = 'active' "
            "ORDER BY u.display_name, p.id",
            (user_id, user_id, user_id),
        ).fetchall()
        modes = cur.execute(
            "SELECT DISTINCT mode FROM letters WHERE sender_id = %s OR recipient_id = %s "
            "ORDER BY mode",
            (user_id, user_id),
        ).fetchall()
        statuses = cur.execute(
            "SELECT DISTINCT status FROM letters WHERE sender_id = %s OR recipient_id = %s "
            "ORDER BY status",
            (user_id, user_id),
        ).fetchall()
    return {
        "recipients": recipients,
        "penpalships": pairs,
        "correspondents": recipients,
        "modes": [row["mode"] for row in modes],
        "statuses": [row["status"] for row in statuses],
    }


def read_report(
    conn, user_id, correspondent_id=None, mode=None, status=None, date_from=None, date_to=None
):
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            MAILBOX_REPORT,
            (
                user_id,
                user_id,
                user_id,
                user_id,
                correspondent_id,
                correspondent_id,
                correspondent_id,
                mode,
                mode,
                status,
                status,
                date_from,
                date_from,
                date_to,
                date_to,
            ),
        ).fetchone()


@router.get("/letters", response_model=list[LetterOut])
def letters(conn: Db, user_id: Identity):
    return read_report(conn, user_id)["letters"]


@router.get("/report", response_model=ReportOut)
def report(
    conn: Db,
    user_id: Identity,
    correspondent_id: int | None = Query(default=None, gt=0),
    mode: Mode | None = None,
    status: Status | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Start date must be on or before end date.")
    if correspondent_id == user_id:
        raise HTTPException(422, "Choose another user as the correspondent.")
    return read_report(conn, user_id, correspondent_id, mode, status, date_from, date_to)


def write_error(exc: IntegrityError):
    # The transaction has already rolled back before this becomes an HTTP error.
    raise HTTPException(
        422,
        "Letter rejected: check the recipient, mode, and pen-palship. "
        "Only matching participants may exchange pen-pal letters.",
    ) from exc


def missing_or_locked(conn, letter_id, user_id):
    row = conn.execute(
        "SELECT status FROM letters WHERE id = %s AND sender_id = %s", (letter_id, user_id)
    ).fetchone()
    if row:
        raise HTTPException(409, "Only your draft letters can be edited or deleted.")
    raise HTTPException(404, "Letter not found among your sent letters.")


@router.post("/letters", response_model=WriteOut, status_code=201)
def create_letter(payload: LetterInput, conn: Db, user_id: Identity):
    try:
        with conn.transaction():
            row = conn.execute(
                CREATE_LETTER,
                (
                    user_id,
                    payload.recipient_id,
                    payload.penpalship_id,
                    payload.subject,
                    payload.body,
                    payload.mode,
                ),
            ).fetchone()
    except IntegrityError as exc:
        write_error(exc)
    return {"id": row[0]}


@router.put("/letters/{letter_id}", response_model=WriteOut)
def update_letter(letter_id: int, payload: LetterInput, conn: Db, user_id: Identity):
    try:
        with conn.transaction():
            row = conn.execute(
                UPDATE_LETTER,
                (
                    payload.recipient_id,
                    payload.penpalship_id,
                    payload.subject,
                    payload.body,
                    payload.mode,
                    letter_id,
                    user_id,
                ),
            ).fetchone()
    except IntegrityError as exc:
        write_error(exc)
    if not row:
        missing_or_locked(conn, letter_id, user_id)
    return {"id": row[0]}


@router.delete("/letters/{letter_id}", status_code=204)
def delete_letter(letter_id: int, conn: Db, user_id: Identity):
    with conn.transaction():
        row = conn.execute(DELETE_LETTER, (letter_id, user_id)).fetchone()
    if not row:
        missing_or_locked(conn, letter_id, user_id)
    return Response(status_code=204)
