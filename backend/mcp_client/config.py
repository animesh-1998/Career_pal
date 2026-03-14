import os
from pathlib import Path

# base path to mcp-servers folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent
HOME_DIR = Path.home()

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
    },
    "email": {
        "command": "node",
        "args": [
            str(BASE_DIR / "backend" / "mcp-server" / "Gmail-MCP-Server" / "dist" / "index.js")
        ],
        "transport": "stdio",
        "env": {
            "GMAIL_OAUTH_PATH": str(HOME_DIR / ".gmail-mcp" / "gcp-oauth.keys.json"),
            "GMAIL_CREDENTIALS_PATH": str(HOME_DIR / ".gmail-mcp" / "credentials.json")
        }
    }
}