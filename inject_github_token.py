#!/usr/bin/env python3
"""Inject GitHub PAT into config.yaml MCP server"""
import yaml, os, re

# Get paths from environment or use defaults
HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")
ENV_PATH = os.environ.get("GITHUB_ENV_FILE", os.path.expanduser("~/.env.github"))

# Read token from environment variable first, then fallback to file
token = os.environ.get("GITHUB_TOKEN")
if not token:
    # Read token from env file
    with open(ENV_PATH) as f:
        env_content = f.read()

    # Extract the actual token
    match = re.search(r'GITHUB_TOKEN=(.+)', env_content)
    if not match:
        print("❌ Could not find GITHUB_TOKEN in .env.github")
        print(f"File content: {repr(env_content)}")
        exit(1)

    token = match.group(1).strip()

print(f"Using token: {token[:20]}...{token[-10:]}")

# Read config
with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

# Update GitHub server
github = cfg["mcp_servers"]["github"]
github["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = token

# Write back
with open(CONFIG_PATH, "w") as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

print("✅ GitHub PAT injected into mcp_servers.github")
