from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

from api.routes.chat import router as chat_router
from mcp_client.config import MCP_SERVERS
import mcp_client as mcp
from agents.graph import build_agent_graph
import agents.graph as agent

from mcp_client.client import init_mcp_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    # init client inside client.py itself
    init_mcp_client()
    print("✅ MCP client ready")

    agent.graph = await build_agent_graph()
    print("✅ Agent graph built")

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

@app.get("/health")
def health():
    return {"status": "ok"}