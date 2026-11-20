import re

from app.config import EMBEDDING_DIM, POLICY_DIR
from app.embeddings import embed_documents, to_pg_vector


def chunk_text(text: str, limit: int = 900) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(current) + len(paragraph) + 2 > limit:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current.strip():
        chunks.append(current.strip())
    return chunks


def load_documents() -> list[dict]:
    documents: list[dict] = []
    for path in sorted(POLICY_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        title_match = re.search(r"^#\s+(.+)$", raw, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        body = raw[title_match.end() :] if title_match else raw
        sections = re.split(r"\n##\s+", body)
        ordinal = 0
        pieces = []
        for section in sections:
            lines = section.strip().split("\n", 1)
            heading = lines[0].strip() if lines else "Overview"
            content = lines[1].strip() if len(lines) > 1 else ""
            if not content:
                continue
            for chunk in chunk_text(content):
                pieces.append(
                    {
                        "section": heading,
                        "ordinal": ordinal,
                        "content": chunk,
                    }
                )
                ordinal += 1
        documents.append({"slug": path.stem, "title": title, "chunks": pieces})
    return documents


def ingest(conn) -> dict:
    documents = load_documents()
    texts: list[str] = []
    for document in documents:
        for chunk in document["chunks"]:
            texts.append(
                f"{document['title']} | {chunk['section']}\n{chunk['content']}"
            )

    vectors = embed_documents(texts)
    if any(len(v) != EMBEDDING_DIM for v in vectors):
        raise RuntimeError("Embedding dimensions do not match the schema")

    conn.execute("DELETE FROM policy_chunks")
    cursor = 0
    for document in documents:
        conn.execute(
            """
            INSERT INTO policy_docs (slug, title, updated_on)
            VALUES (%s, %s, CURRENT_DATE)
            ON CONFLICT (slug) DO UPDATE
            SET title = EXCLUDED.title, updated_on = CURRENT_DATE
            """,
            (document["slug"], document["title"]),
        )
        for chunk in document["chunks"]:
            conn.execute(
                """
                INSERT INTO policy_chunks
                    (doc_slug, doc_title, section, ordinal, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                """,
                (
                    document["slug"],
                    document["title"],
                    chunk["section"],
                    chunk["ordinal"],
                    chunk["content"],
                    to_pg_vector(vectors[cursor]),
                ),
            )
            cursor += 1
    conn.commit()
    return {
        "documents": len(documents),
        "chunks": len(texts),
    }
