-- Stage 2 core schema. No authentication or delivery scheduler.
CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username text NOT NULL UNIQUE CHECK (btrim(username) <> ''),
    email text NOT NULL UNIQUE CHECK (btrim(email) <> ''),
    display_name text NOT NULL CHECK (btrim(display_name) <> ''),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE penpalships (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_a_id bigint NOT NULL REFERENCES users(id),
    user_b_id bigint NOT NULL REFERENCES users(id),
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT canonical_participants CHECK (user_a_id < user_b_id),
    CONSTRAINT unique_participants UNIQUE (user_a_id, user_b_id)
);

CREATE TABLE letters (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sender_id bigint NOT NULL REFERENCES users(id),
    recipient_id bigint NOT NULL REFERENCES users(id),
    penpalship_id bigint REFERENCES penpalships(id),
    subject text NOT NULL CHECK (btrim(subject) <> ''),
    body text NOT NULL CHECK (body !~ '^\s*$'),
    mode text NOT NULL CHECK (mode IN ('direct', 'penpal')),
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'in_transit', 'delivered')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    send_at timestamptz,
    deliver_at timestamptz,
    delivered_at timestamptz,
    CONSTRAINT distinct_correspondents CHECK (sender_id <> recipient_id),
    CONSTRAINT mode_matches_penpalship CHECK (
        (mode = 'penpal' AND penpalship_id IS NOT NULL)
        OR (mode = 'direct' AND penpalship_id IS NULL)
    ),
    CONSTRAINT ordered_delivery CHECK (deliver_at IS NULL OR send_at IS NULL
                                      OR deliver_at >= send_at),
    CONSTRAINT ordered_arrival CHECK (delivered_at IS NULL OR deliver_at IS NULL
                                     OR delivered_at >= deliver_at)
);

CREATE FUNCTION canonicalize_penpalship() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE original_a bigint;
BEGIN
    IF NEW.user_a_id > NEW.user_b_id THEN
        original_a := NEW.user_a_id;
        NEW.user_a_id := NEW.user_b_id;
        NEW.user_b_id := original_a;
    END IF;
    IF TG_OP = 'UPDATE' AND
       (NEW.user_a_id, NEW.user_b_id) IS DISTINCT FROM (OLD.user_a_id, OLD.user_b_id)
       AND EXISTS (SELECT 1 FROM letters WHERE penpalship_id = OLD.id) THEN
        RAISE EXCEPTION 'Cannot change participants of a pen-palship with letters'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER canonicalize_penpalship_row BEFORE INSERT OR UPDATE ON penpalships
FOR EACH ROW EXECUTE FUNCTION canonicalize_penpalship();

CREATE FUNCTION guard_letter() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.status <> 'draft' THEN
        RAISE EXCEPTION 'Only draft letters can be edited or deleted' USING ERRCODE = '23514';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    IF NEW.penpalship_id IS NOT NULL THEN
        -- Hold the pair stable until the letter write commits.
        PERFORM 1 FROM penpalships
        WHERE id = NEW.penpalship_id
          AND user_a_id = least(NEW.sender_id, NEW.recipient_id)
          AND user_b_id = greatest(NEW.sender_id, NEW.recipient_id)
        FOR SHARE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Letter participants must match the selected pen-palship'
                USING ERRCODE = '23514';
        END IF;
    END IF;
    IF TG_OP = 'UPDATE' THEN
        NEW.updated_at := clock_timestamp();
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER guard_letter_row BEFORE INSERT OR UPDATE OR DELETE ON letters
FOR EACH ROW EXECUTE FUNCTION guard_letter();

CREATE FUNCTION letter_word_count(content text) RETURNS integer
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
    SELECT CASE WHEN content IS NULL OR content ~ '^\s*$' THEN 0
        ELSE cardinality(regexp_split_to_array(
            regexp_replace(content, '^\s+|\s+$', '', 'g'), '\s+')) END;
$$;

-- Mailbox/report sender branch, status selection, and creation-date range.
CREATE INDEX letters_sender_report_idx ON letters(sender_id, status, created_at);
-- Mailbox/report recipient branch, status selection, and creation-date range.
CREATE INDEX letters_recipient_report_idx ON letters(recipient_id, status, created_at);
-- Membership protection when changing a pen-palship's participants.
CREATE INDEX letters_penpalship_idx ON letters(penpalship_id);
