from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL, EMBEDDING_DIM

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    manager_id TEXT,
    joined_on DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS leave_balances (
    employee_id TEXT REFERENCES employees(employee_id) ON DELETE CASCADE,
    leave_type TEXT NOT NULL,
    entitled NUMERIC(4, 1) NOT NULL,
    used NUMERIC(4, 1) NOT NULL DEFAULT 0,
    PRIMARY KEY (employee_id, leave_type)
);

CREATE TABLE IF NOT EXISTS policy_docs (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    updated_on DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS policy_chunks (
    id SERIAL PRIMARY KEY,
    doc_slug TEXT REFERENCES policy_docs(slug) ON DELETE CASCADE,
    doc_title TEXT NOT NULL,
    section TEXT NOT NULL,
    ordinal INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector({EMBEDDING_DIM}) NOT NULL,
    UNIQUE (doc_slug, ordinal)
);

CREATE INDEX IF NOT EXISTS policy_chunks_embedding_idx
    ON policy_chunks USING hnsw (embedding vector_cosine_ops);
"""


def connect():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=15,
        keepalives=1,
    )


@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema(conn) -> None:
    conn.execute(SCHEMA)
    conn.commit()


def search_policy(conn, vector_literal: str, limit: int, min_score: float) -> list[dict]:
    return conn.execute(
        """
        SELECT doc_slug, doc_title, section, content,
               1 - (embedding <=> %s::vector) AS score
        FROM policy_chunks
        WHERE 1 - (embedding <=> %s::vector) >= %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (vector_literal, vector_literal, min_score, vector_literal, limit),
    ).fetchall()
