#!/usr/bin/env python3
"""Add MCP servers to config.yaml"""
import yaml, os

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")
HOME_DIR = os.path.expanduser("~")

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

mcp = cfg.setdefault("mcp_servers", {})

# 1. Time server
mcp["time"] = {
    "command": "uvx",
    "args": ["mcp-server-time"],
    "timeout": 120,
    "connect_timeout": 60,
}

# 2. Filesystem server
mcp["filesystem"] = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", HOME_DIR],
    "timeout": 30,
    "connect_timeout": 60,
}

# 3. Brave Search
mcp["brave-search"] = {
    "command": "npx",
    "args": ["-y", "@anthropic/server-brave-search"],
    "env": {
        "BRAVE_API_KEY": "YOUR_BRAVE_API_KEY_HERE"
    },
    "timeout": 60,
    "connect_timeout": 60,
}

# 4. GitHub
mcp["github"] = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_GITHUB_TOKEN_HERE"
    },
    "timeout": 60,
    "connect_timeout": 60,
}

# 5. Fetch (HTML → Markdown)
mcp["fetch"] = {
    "command": "uvx",
    "args": ["mcp-server-fetch"],
    "timeout": 60,
    "connect_timeout": 60,
}

with open(CONFIG_PATH, "w") as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print("✅ Done! Added 5 MCP servers:")
for name in ["time", "filesystem", "brave-search", "github", "fetch"]:
    print(f"  - {name}")
