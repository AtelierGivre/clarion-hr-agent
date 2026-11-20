import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

POLICY_DIR = ROOT / "data" / "policies"
MCP_SERVER = ROOT / "app" / "mcp_server.py"

TOP_K = 5
MIN_SCORE = 0.55
MAX_TOOL_ROUNDS = 3
