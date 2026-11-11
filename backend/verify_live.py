"""Acceptance checks against the running local API and PostgreSQL.

Run from backend: .venv/bin/python verify_live.py
One disposable draft is removed in finally; failed trigger probes roll back.
"""

from decimal import Decimal, ROUND_HALF_UP

import httpx
import psycopg

from app.config import settings


def main():
    with (
        httpx.Client(base_url="http://127.0.0.1:8000/api", timeout=10) as api,
        psycopg.connect(settings.database_url, autocommit=True) as db,
    ):
        assert api.get("/health").json()["status"] == "ok"
        users = api.get("/users").json()
        assert [u["id"] for u in users] == [
            r[0] for r in db.execute("SELECT id FROM users ORDER BY display_name,id").fetchall()
        ]
        actor = next(u["id"] for u in users if u["username"] == "ruhaan")
        params = {"user_id": actor}
        options = api.get("/options", params=params).json()
        assert [u["id"] for u in options["recipients"]] == [
            r[0]
            for r in db.execute(
                "SELECT id FROM users WHERE id<>%s ORDER BY display_name,id", (actor,)
            ).fetchall()
        ]
        for key, query in [
            (
                "modes",
                "SELECT DISTINCT mode FROM letters WHERE sender_id=%s OR recipient_id=%s "
                "ORDER BY mode",
            ),
            (
                "statuses",
                "SELECT DISTINCT status FROM letters WHERE sender_id=%s OR recipient_id=%s "
                "ORDER BY status",
            ),
        ]:
            assert options[key] == [r[0] for r in db.execute(query, (actor, actor)).fetchall()]
        keys = ("matching_count", "average_word_count", "sent_count", "received_count")

        def report(filters=None):
            result = api.get("/report", params={**params, **(filters or {})})
            result.raise_for_status()
            return result.json()

        baseline = report()
        print("Initial:", {k: baseline[k] for k in keys})
        total = db.execute(
            "SELECT coalesce(sum(letter_word_count(body)),0) FROM letters "
            "WHERE sender_id=%s OR recipient_id=%s",
            (actor, actor),
        ).fetchone()[0]
        draft = {
            "recipient_id": options["recipients"][0]["id"],
            "mode": "direct",
            "penpalship_id": None,
            "subject": "Disposable live acceptance draft",
            "body": "one two three four five",
        }
        letter_id = None
        try:
            response = api.post("/letters", params=params, json=draft)
            assert response.status_code == 201, response.text
            letter_id = response.json()["id"]
            assert db.execute(
                "SELECT status,letter_word_count(body) FROM letters WHERE id=%s", (letter_id,)
            ).fetchone() == ("draft", 5)
            created = report()
            assert created["matching_count"] == baseline["matching_count"] + 1
            assert letter_id in [r["id"] for r in created["letters"]]
            print("Created:", {k: created[k] for k in keys})
            draft["body"] = " ".join(["word"] * 20)
            assert api.put(f"/letters/{letter_id}", params=params, json=draft).status_code == 200
            edited = report()
            expected = (Decimal(total + 20) / Decimal(baseline["matching_count"] + 1)).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
            assert Decimal(str(edited["average_word_count"])) == expected
            assert (
                db.execute(
                    "SELECT letter_word_count(body) FROM letters WHERE id=%s", (letter_id,)
                ).fetchone()[0]
                == 20
            )
            print("Edited:", {k: edited[k] for k in keys})
        finally:
            if letter_id:
                assert api.delete(f"/letters/{letter_id}", params=params).status_code == 204
        restored = report()
        assert {k: restored[k] for k in keys} == {k: baseline[k] for k in keys}
        assert not db.execute("SELECT id FROM letters WHERE id=%s", (letter_id,)).fetchone()
        print("Deleted:", {k: restored[k] for k in keys})
        cases = [
            (
                {"correspondent_id": draft["recipient_id"]},
                "SELECT count(*) FROM letters WHERE (sender_id=%s OR recipient_id=%s) "
                "AND (sender_id=%s OR recipient_id=%s)",
                (actor, actor, draft["recipient_id"], draft["recipient_id"]),
            ),
            (
                {"mode": "penpal"},
                "SELECT count(*) FROM letters WHERE (sender_id=%s OR recipient_id=%s) AND mode=%s",
                (actor, actor, "penpal"),
            ),
            (
                {"status": "delivered"},
                "SELECT count(*) FROM letters WHERE "
                "(sender_id=%s OR recipient_id=%s) AND status=%s",
                (actor, actor, "delivered"),
            ),
            (
                {"date_from": "2026-10-20", "date_to": "2026-11-01"},
                "SELECT count(*) FROM letters WHERE (sender_id=%s OR recipient_id=%s) "
                "AND created_at >= %s AND created_at < %s",
                (actor, actor, "2026-10-20T00:00:00Z", "2026-11-02T00:00:00Z"),
            ),
        ]
        for filters, query, values in cases:
            result = report(filters)
            assert result["matching_count"] == db.execute(query, values).fetchone()[0]
            assert result["matching_count"] == len(result["letters"])
            print("Filter:", filters, "=>", result["matching_count"])
        pair = options["penpalships"][0]
        wrong = next(r["id"] for r in options["recipients"] if r["id"] != pair["correspondent_id"])
        invalid = {**draft, "recipient_id": wrong, "mode": "penpal", "penpalship_id": pair["id"]}
        assert api.post("/letters", params=params, json=invalid).status_code == 422
        for status in ("in_transit", "delivered"):
            row = db.execute(
                "SELECT id FROM letters WHERE sender_id=%s AND status=%s LIMIT 1", (actor, status)
            ).fetchone()
            assert row, "Seed must include outgoing letters in both immutable statuses"
            assert api.put(f"/letters/{row[0]}", params=params, json=draft).status_code == 409
            assert api.delete(f"/letters/{row[0]}", params=params).status_code == 409
            for statement in (
                "UPDATE letters SET body='forbidden' WHERE id=%s",
                "DELETE FROM letters WHERE id=%s",
            ):
                try:
                    with db.transaction():
                        db.execute(statement, row)
                except psycopg.errors.CheckViolation:
                    pass
                else:
                    raise AssertionError("Immutable-letter database trigger did not reject write")
        assert {k: report()[k] for k in keys} == {k: baseline[k] for k in keys}
        print("PASS: live CRUD, SQL persistence, aggregates, filters, DB options, invalid")
        print("associations, immutable API writes, and direct-SQL trigger rejection.")


if __name__ == "__main__":
    main()
