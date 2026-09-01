-- 001_initial.sql
-- yoyo-migrations plain-SQL format: this file holds the forward ("apply")
-- SQL. Its rollback lives in the paired 001_initial.rollback.sql file --
-- yoyo pairs a migration with rollback SQL purely by matching filename
-- stem, not by any marker inside the file.
--
-- This is a deliberately trivial table -- Stage 1 only needs to prove that
-- migrations run against a real Postgres database. The real schema comes
-- once the application domain is chosen.

CREATE TABLE stack_check (
    id          SERIAL PRIMARY KEY,
    note        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO stack_check (note) VALUES ('yoyo-migrations is wired up correctly');
