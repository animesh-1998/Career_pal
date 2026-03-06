import os
from pathlib import Path

# base path to mcp-servers folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent

print(f"MCP_SERVERS_DIR: {BASE_DIR}")

MCP_SERVERS = {
    "linkedin": {
        "command": "uv",
        "args": [
            "run",
            "--directory", str(BASE_DIR / "backend" / "mcp-server" / "linkedin-mcp-server"),
            "-m", "linkedin_mcp_server",
            "--transport", "stdio"      # ← skip the interactive prompt
        ],
        "transport": "stdio"
    }
}