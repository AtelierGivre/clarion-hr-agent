import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pgserver
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

database = pgserver.get_server(ROOT / ".pgdata", cleanup_mode="stop")
os.environ["DATABASE_URL"] = database.get_uri()

from app.db import ensure_schema, get_conn  # noqa: E402
from app.ingest import ingest  # noqa: E402
from scripts.seed import seed_employees  # noqa: E402

if __name__ == "__main__":
    with get_conn() as conn:
        ensure_schema(conn)
        seed_employees(conn)
        count = conn.execute("SELECT count(*) AS n FROM policy_chunks").fetchone()["n"]
        if count == 0:
            print("Embedding policy documents for the first time...")
            print(ingest(conn))

    print(f"Postgres ready at {database.get_uri()}")
    print("Open http://127.0.0.1:8000")

    import uvicorn

    uvicorn.run("api.index:app", host="127.0.0.1", port=8000)
