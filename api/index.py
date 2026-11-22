import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config
from app.adk_agent import run_adk_agent
from app.agent import run_agent
from app.db import get_conn

app = FastAPI(title="Clarion", docs_url="/api/docs", openapi_url="/api/openapi.json")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    employee_id: str = Field(default="E102", pattern=r"^E\d{3}$")
    provider: str = Field(default="gemini", pattern=r"^(gemini|anthropic|openai)$")


def _employee(employee_id: str) -> dict | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT employee_id, name, department FROM employees WHERE employee_id = %s",
            (employee_id,),
        ).fetchone()


@app.get("/api/health")
def health() -> dict:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        database = "ok"
    except Exception:
        database = "down"
    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
        "model": config.GEMINI_MODEL,
        "embedding_model": config.EMBEDDING_MODEL,
        "provider": config.LLM_PROVIDER,
        "providers": list(config.PROVIDERS),
    }


@app.get("/api/employees")
def employees() -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT employee_id, name, department FROM employees ORDER BY employee_id"
        ).fetchall()
    return {"employees": rows}


async def _answer(request: ChatRequest, engine: str) -> dict:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please type a question.")

    employee = _employee(request.employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    try:
        if engine == "adk":
            result = await run_adk_agent(message, request.employee_id, request.provider)
        else:
            result = await run_agent(message, request.employee_id, request.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"agent error: {type(exc).__name__}: {exc}", flush=True)
        raise HTTPException(
            status_code=503, detail="The agent is busy. Please try again in a moment."
        ) from exc

    result["employee"] = {"id": employee["employee_id"], "name": employee["name"]}
    result["question"] = message
    return result


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict:
    """Answer with the LangGraph agent."""
    return await _answer(request, "langgraph")


@app.post("/api/chat/adk")
async def chat_adk(request: ChatRequest) -> dict:
    """Answer with the Google ADK agent."""
    return await _answer(request, "adk")


if (ROOT / "public").is_dir():
    app.mount("/", StaticFiles(directory=ROOT / "public", html=True), name="static")
