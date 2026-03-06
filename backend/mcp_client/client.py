from langchain_mcp_adapters.client import MultiServerMCPClient
from .config import MCP_SERVERS

_client: MultiServerMCPClient | None = None

def init_mcp_client():
    global _client
    _client = MultiServerMCPClient(MCP_SERVERS)
    return _client

def get_mcp_client() -> MultiServerMCPClient:
    if _client is None:
        raise RuntimeError("MCP client not initialized. Check lifespan in main.py")
    return _client

async def get_tools(servers: list[str] = None) -> list:
    client = get_mcp_client()
    all_tools = await client.get_tools()

    if servers is None:
        return all_tools

    return [
        tool for tool in all_tools
        if any(server in tool.name for server in servers)
    ]