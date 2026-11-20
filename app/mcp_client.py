import os
import sys
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from app.config import DATABASE_URL, MCP_SERVER, ROOT

SERVER_NAME = "hr"


@asynccontextmanager
async def hr_tools():
    env = {**os.environ, "DATABASE_URL": DATABASE_URL}
    # Reuse the parent interpreter's import paths so the child can find the
    # bundled dependencies on serverless hosts such as Vercel.
    env["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys([str(ROOT), *[p for p in sys.path if p]])
    )
    client = MultiServerMCPClient(
        {
            SERVER_NAME: {
                "command": sys.executable,
                "args": [str(MCP_SERVER)],
                "cwd": str(ROOT),
                "transport": "stdio",
                "env": env,
            }
        }
    )
    async with client.session(SERVER_NAME) as session:
        yield await load_mcp_tools(session)
