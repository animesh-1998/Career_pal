from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes.chat import router as chat_router
from api.routes.auth import router as auth_router
from api.routes.sessions import router as sessions_router

from mcp_client.client import init_mcp_client
from agents.graph import build_agent_graph
import agents.graph as agent
from memory.checkpointer import setup_checkpointer
from memory import SessionStore

import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    # ── MCP client ───────────────────────────────────────────────
    init_mcp_client()
    print("MCP client ready")

    # ── Memory / checkpointer ────────────────────────────────────
    checkpointer = await setup_checkpointer()
    agent.checkpointer = checkpointer
    agent.session_store = SessionStore(checkpointer)

    # ── Build agent graph ────────────────────────────────────────
    # Tools are fetched and cleaned inside build_agent_graph now
    agent.graph = await build_agent_graph(checkpointer)
    print("Agent graph built")

    yield

    print("Shutting down...")


app = FastAPI(
    title="AI Assistant",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])


@app.get("/health")
def health():
    return {"status": "ok"}