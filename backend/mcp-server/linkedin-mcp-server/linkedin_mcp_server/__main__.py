#!/usr/bin/env python3
"""Entry point for linkedin-mcp-server command."""

from linkedin_mcp_server.cli_main import main
import sys
import io

# force UTF-8 encoding on Windows stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

if __name__ == "__main__":
    main()
