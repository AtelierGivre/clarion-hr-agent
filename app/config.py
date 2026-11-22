import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Which provider the LangGraph and ADK agents use by default.
# One of: gemini, anthropic, openai.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
PROVIDERS = ("gemini", "anthropic", "openai")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

POLICY_DIR = ROOT / "data" / "policies"
MCP_SERVER = ROOT / "app" / "mcp_server.py"

TOP_K = 5
MIN_SCORE = 0.55
MAX_TOOL_ROUNDS = 3
