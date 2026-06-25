#!/usr/bin/env python3
"""Patch config.yaml: update Cloudflare token, add GitHub Models & OpenRouter.

NOTE: This script contains example placeholders. Replace with your own credentials.
"""
import re
import os

# Get paths from environment or use defaults
HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")

with open(CONFIG_PATH) as f:
    content = f.read()

# 1. Update Cloudflare token (use environment variable)
CLOUDFLARE_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "YOUR_CLOUDFLARE_TOKEN_HERE")
OLD_TOKEN = os.environ.get("OLD_CLOUDFLARE_TOKEN", "")
if OLD_TOKEN:
    content = content.replace(OLD_TOKEN, CLOUDFLARE_TOKEN)

# 2. Update Cloudflare base_url (add /v1)
OLD_CF_URL = os.environ.get("OLD_CLOUDFLARE_URL", "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/")
NEW_CF_URL = os.environ.get("CLOUDFLARE_BASE_URL", "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/v1")
content = content.replace(OLD_CF_URL, NEW_CF_URL)

# 3. Add GitHub Models and OpenRouter after the Translation Proxy entry
old_block = '''  name: "Translation Proxy (JA↔EN)"
group_sessions_per_user: true'''

# Use environment variables for API keys
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "YOUR_OPENROUTER_KEY_HERE")

new_block = f'''  name: "Translation Proxy (JA↔EN)"
- api_key: {GITHUB_TOKEN}
  base_url: https://models.inference.ai.azure.com
  model: gpt-4o-mini
  name: GitHub Models
- api_key: {OPENROUTER_KEY}
  base_url: https://openrouter.ai/api/v1
  model: deepseek/deepseek-v4-flash
  name: OpenRouter
group_sessions_per_user: true'''

content = content.replace(old_block, new_block)

with open("/home/nsh1l/.hermes/config.yaml", "w") as f:
    f.write(content)

print("✅ Config updated successfully!")
