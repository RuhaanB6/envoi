from datetime import datetime, timezone

import psycopg
import pytest


def payload(recipient, **changes):
    return {
        "recipient_id": recipient,
        "mode": "direct",
        "penpalship_id": None,
        "subject": "Hello",
        "body": "one two",
        **changes,
    }


def insert_letter(db, sender, recipient, **changes):
    data = {
        "mode": "direct",
        "penpalship_id": None,
        "subject": "Test letter",
        "body": "one two",
        "status": "draft",
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        **changes,
    }
    return db.execute(
        "INSERT INTO letters(sender_id,recipient_id,mode,penpalship_id,subject,body,status,"
        "created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
        (
            sender,
            recipient,
            data["mode"],
            data["penpalship_id"],
            data["subject"],
            data["body"],
            data["status"],
            data["created_at"],
        ),
    ).fetchone()[0]


def test_canonical_pairs_reject_reversed_duplicates(db, people, pair):
    assert db.execute(
        "SELECT user_a_id,user_b_id FROM penpalships WHERE id=%s", (pair,)
    ).fetchone() == (people[0], people[1])
    with pytest.raises(psycopg.errors.UniqueViolation):
        db.execute(
            "INSERT INTO penpalships(user_a_id,user_b_id) VALUES (%s,%s)", (people[1], people[0])
        )
    row = db.execute(
        "INSERT INTO penpalships(user_a_id,user_b_id) VALUES (%s,%s) RETURNING user_a_id,user_b_id",
        (people[3], people[2]),
    ).fetchone()
    assert row == (people[2], people[3])


def test_pair_cannot_contain_same_user(db, people):
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute(
            "INSERT INTO penpalships(user_a_id,user_b_id) VALUES (%s,%s)", (people[0], people[0])
        )


@pytest.mark.parametrize(
    "change",
    [
        {"sender_id": 999999},
        {"recipient_id": 999999},
        {"sender_id": None},
        {"recipient_id": None},
        {"mode": "penpal", "penpalship_id": None},
        {"mode": "unknown"},
        {"status": "unknown"},
        {"body": " \t\n "},
        {"subject": " "},
    ],
)
def test_database_rejects_invalid_letters(db, people, change):
    sender = change.pop("sender_id", people[0])
    recipient = change.pop("recipient_id", people[1])
    with pytest.raises(psycopg.IntegrityError):
        insert_letter(db, sender, recipient, **change)


def test_database_rejects_self_letter(db, people):
    with pytest.raises(psycopg.errors.CheckViolation):
        insert_letter(db, people[0], people[0])


def test_membership_and_mode_are_enforced_in_database(db, people, pair):
    with pytest.raises(psycopg.errors.CheckViolation):
        insert_letter(db, people[0], people[2], mode="penpal", penpalship_id=pair)
    with pytest.raises(psycopg.errors.CheckViolation):
        insert_letter(db, people[0], people[1], mode="direct", penpalship_id=pair)
    letter = insert_letter(db, people[1], people[0], mode="penpal", penpalship_id=pair)
    assert letter > 0
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute("UPDATE penpalships SET user_b_id=%s WHERE id=%s", (people[2], pair))
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute("UPDATE letters SET recipient_id=%s WHERE id=%s", (people[2], letter))


@pytest.mark.parametrize("status", ["in_transit", "delivered"])
def test_non_drafts_immutable_even_through_sql(db, people, status):
    letter = insert_letter(db, *people[:2], status=status)
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute("UPDATE letters SET body=%s WHERE id=%s", ("changed", letter))
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute("DELETE FROM letters WHERE id=%s", (letter,))


def test_sql_word_counts_handle_whitespace(db):
    for body, expected in [
        ("", 0),
        (" \t\n ", 0),
        (" one  two\nthree\t ", 3),
        ("hello-world", 1),
        (None, 0),
    ]:
        assert db.execute("SELECT letter_word_count(%s)", (body,)).fetchone()[0] == expected


def test_crud_changes_report_and_options(client, db, people):
    a, b = people[:2]
    params = {"user_id": a}
    assert client.get("/api/report", params=params).json()["matching_count"] == 0
    assert client.get("/api/options", params=params).json()["modes"] == []
    response = client.post("/api/letters", params=params, json=payload(b))
    assert response.status_code == 201, response.text
    letter = response.json()["id"]
    report = client.get("/api/report", params=params).json()
    assert (
        report["matching_count"],
        report["average_word_count"],
        report["sent_count"],
        report["received_count"],
    ) == (1, 2, 1, 0)
    assert report["letters"][0]["can_edit"] is True
    assert report["letters"][0]["status"] == "draft"
    assert client.get("/api/options", params=params).json()["modes"] == ["direct"]
    before = report["letters"][0]["updated_at"]
    response = client.put(
        f"/api/letters/{letter}",
        params=params,
        json=payload(b, body="one two three four", subject="Revised"),
    )
    assert response.status_code == 200
    report = client.get("/api/report", params=params).json()
    assert report["average_word_count"] == 4
    assert report["letters"][0]["subject"] == "Revised"
    assert report["letters"][0]["updated_at"] != before
    received = client.get("/api/letters", params={"user_id": b}).json()
    assert received[0]["can_edit"] is False
    assert client.delete(f"/api/letters/{letter}", params=params).status_code == 204
    report = client.get("/api/report", params=params).json()
    assert (report["matching_count"], report["average_word_count"], report["letters"]) == (0, 0, [])
    assert client.get("/api/options", params=params).json()["statuses"] == []


def test_other_users_cannot_modify_letter(client, db, people):
    letter = insert_letter(db, *people[:2])
    for actor in people[1:]:
        assert (
            client.put(
                f"/api/letters/{letter}", params={"user_id": actor}, json=payload(people[0])
            ).status_code
            == 404
        )
        assert client.delete(f"/api/letters/{letter}", params={"user_id": actor}).status_code == 404
    assert len(client.get("/api/letters", params={"user_id": people[2]}).json()) == 0


@pytest.mark.parametrize("status", ["in_transit", "delivered"])
def test_api_rejects_non_draft_writes(client, db, people, status):
    letter = insert_letter(db, *people[:2], status=status)
    assert (
        client.put(
            f"/api/letters/{letter}", params={"user_id": people[0]}, json=payload(people[1])
        ).status_code
        == 409
    )
    assert client.delete(f"/api/letters/{letter}", params={"user_id": people[0]}).status_code == 409


def test_api_rejects_invalid_associations_and_extra_status(client, people, pair):
    for data in [
        payload(people[0]),
        payload(999999),
        payload(people[1], mode="penpal"),
        payload(people[2], mode="penpal", penpalship_id=pair),
        payload(people[1], penpalship_id=pair),
        payload(people[1], status="delivered"),
        payload(people[1], body=" "),
    ]:
        response = client.post("/api/letters", params={"user_id": people[0]}, json=data)
        assert response.status_code == 422, response.text
    good = client.post(
        "/api/letters",
        params={"user_id": people[1]},
        json=payload(people[0], mode="penpal", penpalship_id=pair),
    )
    assert good.status_code == 201


def test_filter_options_come_from_database(client, db, people, pair):
    a, b, c, _ = people
    insert_letter(db, a, b, mode="penpal", penpalship_id=pair, status="delivered")
    options = client.get("/api/options", params={"user_id": a}).json()
    assert {r["id"] for r in options["recipients"]} == set(people[1:])
    assert options["penpalships"][0]["correspondent_id"] == b
    assert options["modes"] == ["penpal"]
    assert options["statuses"] == ["delivered"]
    db.execute(
        "INSERT INTO users(username,email,display_name) VALUES (%s,%s,%s)",
        ("new", "new@example.test", "New person"),
    )
    assert len(client.get("/api/options", params={"user_id": a}).json()["recipients"]) == 4
    assert client.get("/api/options", params={"user_id": c}).json()["penpalships"] == []


@pytest.fixture
def report_data(db, people, pair):
    a, b, c, d = people
    first = insert_letter(db, a, b)
    second = insert_letter(
        db,
        b,
        a,
        mode="penpal",
        penpalship_id=pair,
        body="one two three four",
        status="in_transit",
        created_at=datetime(2026, 1, 2, 23, 59, tzinfo=timezone.utc),
    )
    third = insert_letter(
        db,
        a,
        c,
        body="one two three four five six",
        status="delivered",
        created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )
    insert_letter(db, d, b, body="unrelated")
    return first, second, third


@pytest.mark.parametrize(
    "filters,expected_ids",
    [
        ({}, [0, 1, 2]),
        ({"mode": "penpal"}, [1]),
        ({"status": "delivered"}, [2]),
        ({"date_from": "2026-01-02", "date_to": "2026-01-02"}, [1]),
        ({"date_to": "2026-01-01"}, [0]),
        ({"date_from": "2026-01-03"}, [2]),
        ({"mode": "direct", "status": "draft", "date_to": "2026-01-01"}, [0]),
        ({"date_from": "2027-01-01"}, []),
    ],
)
def test_report_filters(client, people, report_data, filters, expected_ids):
    response = client.get("/api/report", params={"user_id": people[0], **filters})
    assert response.status_code == 200, response.text
    report = response.json()
    assert {r["id"] for r in report["letters"]} == {report_data[i] for i in expected_ids}
    assert report["matching_count"] == len(expected_ids)
    assert report["sent_count"] + report["received_count"] == report["matching_count"]
    if not filters:
        assert report["average_word_count"] == 4
        assert (report["sent_count"], report["received_count"]) == (2, 1)
    if not expected_ids:
        assert report["average_word_count"] == 0


def test_correspondent_filter_covers_both_directions(client, people, report_data):
    response = client.get(
        "/api/report", params={"user_id": people[0], "correspondent_id": people[1]}
    )
    assert response.json()["matching_count"] == 2
    assert response.json()["average_word_count"] == 3
    assert {r["id"] for r in response.json()["letters"]} == set(report_data[:2])


@pytest.mark.parametrize(
    "params",
    [
        {"date_from": "2026-02-01", "date_to": "2026-01-01"},
        {"mode": "invalid"},
        {"status": "invalid"},
        {"date_from": "not-a-date"},
    ],
)
def test_invalid_report_filters_are_rejected(client, people, params):
    assert client.get("/api/report", params={"user_id": people[0], **params}).status_code == 422


def test_unknown_or_missing_identity(client):
    assert client.get("/api/report", params={"user_id": 999999}).status_code == 404
    assert client.get("/api/report").status_code == 422


def test_invalid_edit_is_atomic(client, db, people, pair):
    letter = insert_letter(db, people[0], people[1], mode="penpal", penpalship_id=pair)
    response = client.put(
        f"/api/letters/{letter}",
        params={"user_id": people[0]},
        json=payload(people[2], mode="penpal", penpalship_id=pair, subject="Must not persist"),
    )
    assert response.status_code == 422
    assert db.execute(
        "SELECT recipient_id,subject FROM letters WHERE id=%s", (letter,)
    ).fetchone() == (people[1], "Test letter")


def test_foreign_keys_preserve_referenced_users_and_pairs(db, people, pair):
    insert_letter(db, people[0], people[1], mode="penpal", penpalship_id=pair)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute("DELETE FROM users WHERE id=%s", (people[0],))
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.execute("DELETE FROM penpalships WHERE id=%s", (pair,))
