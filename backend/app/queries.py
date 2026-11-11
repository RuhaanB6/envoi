"""Hand-written SQL for the Stage 2 mailbox. Values always use psycopg parameters."""

# Every join is to one primary-key row. The OR includes each letter only once.
MAILBOX_REPORT = """
WITH matching AS (
    SELECT l.*, s.display_name AS sender_name, r.display_name AS recipient_name,
           letter_word_count(l.body) AS word_count,
           l.sender_id = %s AS is_sent,
           (l.sender_id = %s AND l.status = 'draft') AS can_edit
    FROM letters l
    JOIN users s ON s.id = l.sender_id
    JOIN users r ON r.id = l.recipient_id
    WHERE (l.sender_id = %s OR l.recipient_id = %s)
      AND (%s::bigint IS NULL OR l.sender_id = %s OR l.recipient_id = %s)
      AND (%s::text IS NULL OR l.mode = %s)
      AND (%s::text IS NULL OR l.status = %s)
      AND (%s::date IS NULL OR l.created_at >= (%s::date)::timestamp AT TIME ZONE 'UTC')
      AND (%s::date IS NULL OR l.created_at < (%s::date + 1)::timestamp AT TIME ZONE 'UTC')
)
SELECT count(*) AS matching_count,
       coalesce(round(avg(word_count), 1), 0) AS average_word_count,
       count(*) FILTER (WHERE is_sent) AS sent_count,
       count(*) FILTER (WHERE NOT is_sent) AS received_count,
       coalesce(jsonb_agg(to_jsonb(matching) ORDER BY created_at DESC, id DESC),
                '[]'::jsonb) AS letters
FROM matching
"""

CREATE_LETTER = """
INSERT INTO letters(sender_id, recipient_id, penpalship_id, subject, body, mode, status)
VALUES (%s, %s, %s, %s, %s, %s, 'draft')
RETURNING id
"""

UPDATE_LETTER = """
UPDATE letters SET recipient_id = %s, penpalship_id = %s, subject = %s,
                   body = %s, mode = %s
WHERE id = %s AND sender_id = %s AND status = 'draft'
RETURNING id
"""

DELETE_LETTER = """
DELETE FROM letters WHERE id = %s AND sender_id = %s AND status = 'draft'
RETURNING id
"""
