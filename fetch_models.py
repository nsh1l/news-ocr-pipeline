#!/usr/bin/env python3
"""Fetch latest models from all configured providers."""
import json, subprocess, os, re

HOME = os.path.expanduser("~")

def read_env(var_name, filepath):
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith(var_name + "="):
                    return line.split("=", 1)[1]
    except: pass
    # fallback: .hermes/.env
    try:
        with open(os.path.join(HOME, ".hermes", ".env")) as f:
            for line in f:
                line = line.strip()
                if line.startswith(var_name + "="):
                    return line.split("=", 1)[1]
    except: pass
    return ""

def curl(url, auth_header=None):
    cmd = ["curl", "-s"]
    if auth_header:
        cmd += ["-H", auth_header]
    cmd.append(url)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout)
    except Exception as e:
        return {"error": str(e)}

# ── 1. Google Gemini ──
print("=" * 60)
print("☀️  Google Gemini")
print("=" * 60)
key = read_env("GOOGLE_API_KEY", os.path.join(HOME, ".hermes", ".env"))
if key:
    data = curl(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
    for m in data.get("models", []):
        name = m["name"].replace("models/", "")
        if any(x in name for x in ["embedding", "answer", "search", "grounding", "factuality", "aqa", "tts"]):
            continue
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" in methods:
            limit = m.get("inputTokenLimit", "?")
            print(f"  {name:40s} ctx:{limit:>8,}")

# ── 2. OpenRouter (under $5/M tokens) ──
print("\n" + "=" * 60)
print("🎯  OpenRouter (under $5/M tok)")
print("=" * 60)
or_key = read_env("OPENROUTER_API_KEY", os.path.join(HOME, ".env.openrouter"))
if or_key:
    data = curl("https://openrouter.ai/api/v1/models", f"Authorization: Bearer {or_key}")
    models = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        pricing = m.get("pricing", {})
        prompt = float(pricing.get("prompt", 99))
        completion = float(pricing.get("completion", 99))
        ctx = m.get("context_length", 0)
        if prompt < 5 and completion < 5:
            models.append((mid, prompt, completion, ctx))
    models.sort(key=lambda x: x[1])
    for mid, p, c, ctx in models[:30]:
        print(f"  {mid:55s} ${p:.4f}/${c:.4f}  ctx:{ctx:>8,}")

# ── 3. GitHub Models ──
print("\n" + "=" * 60)
print("🐙  GitHub Models (Free)")
print("=" * 60)
gh_key = read_env("GITHUB_TOKEN", os.path.join(HOME, ".env.github-models"))
if gh_key:
    data = curl("https://models.inference.ai.azure.com/models", f"Authorization: Bearer {gh_key}")
    if isinstance(data, list):
        for m in data:
            mid = m.get("id", "")
            print(f"  {mid}")

# ── 4. Cloudflare Workers AI ──
print("\n" + "=" * 60)
print("☁️  Cloudflare Workers AI (highlights)")
print("=" * 60)
cf_key = read_env("CLOUDFLARE_API_TOKEN", os.path.join(HOME, ".hermes", ".env"))
cf_account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "YOUR_ACCOUNT_ID")
if cf_key:
    data = curl(
        f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/models/search?per_page=100",
        f"Authorization: Bearer {cf_key}"
    )
    if data.get("success"):
        for m in data.get("result", []):
            name = m.get("name", m.get("id", ""))
            task = m.get("task", "")
            # Only chat/text gen / image models
            if any(k in name.lower() for k in ["llama", "qwen", "deepseek", "kimi", "phi", "gemma", "flux", "mistral", "gpt", "deepcoder", "command", "glm"]):
                print(f"  {name:55s} {task}")
        print(f"\n  ... ({data.get('result_info', {}).get('total_count', '?')} total models)")
    else:
        print(f"  Error: {data}")

# ── 5. Existing custom providers from config ──
print("\n" + "=" * 60)
print("📋  Custom Providers in config.yaml")
print("=" * 60)
try:
    with open(os.path.join(HOME, ".hermes", "config.yaml")) as f:
        content = f.read()
    # Parse custom_providers section
    import yaml
    cfg = yaml.safe_load(content)
    for cp in cfg.get("custom_providers", []):
        name = cp.get("name", "?")
        url = cp.get("base_url", "?")
        model = cp.get("model", "?")
        klen = len(str(cp.get("api_key", "")))
        print(f"  {name:30s} model: {model:35s} key: {klen} chars")
        print(f"  {'':30s} url: {url}")
except Exception as e:
    print(f"  Error: {e}")

print("\n✅ Done!")
