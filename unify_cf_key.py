#!/usr/bin/env python3
"""Unify Cloudflare API key: use working cfut token from config.yaml in .env"""
import re

# Read working key from config.yaml
with open("/home/nsh1l/.hermes/config.yaml") as f:
    cfg = f.read()

match = re.search(r'cfut_[a-zA-Z0-9]+', cfg)
if not match:
    print("❌ No cfut token found in config.yaml!")
    exit(1)
cfut_key = match.group(0)
print(f"Config key: {cfut_key[:10]}...{cfut_key[-6:]} ({len(cfut_key)} chars)")

# Read .env
with open("/home/nsh1l/.hermes/.env") as f:
    env = f.read()

# Replace CLOUDFLARE_API_TOKEN line
old_count = env.count("CLOUDFLARE_API_TOKEN=")
env = re.sub(
    r"^CLOUDFLARE_API_TOKEN=.*$",
    f"CLOUDFLARE_API_TOKEN={cfut_key}",
    env,
    count=1,
    flags=re.MULTILINE
)

with open("/home/nsh1l/.hermes/.env", "w") as f:
    f.write(env)

print(f"✅ Replaced CLOUDFLARE_API_TOKEN in .env ({old_count} → 1)")

# Test the unified key
import subprocess, json
url = "https://api.cloudflare.com/client/v4/accounts/83398e0c965426307de219b63f7b1ec4/ai/models/search?per_page=3"
r = subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer *** url],
                   capture_output=True, text=True, timeout=15)
data = json.loads(r.stdout)
if data.get("success"):
    print("✅ API test: WORKS!")
else:
    print(f"❌ API test: Failed - {data.get('errors')}")
