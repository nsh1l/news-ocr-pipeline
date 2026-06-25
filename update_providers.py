#!/usr/bin/env python3
"""
Update providers section and custom_providers models lists in config.yaml.
Adds curated model lists to Cloudflare and GitHub Models custom providers.
"""
import yaml
import copy

with open("/home/nsh1l/.hermes/config.yaml", "r") as f:
    raw = f.read()

# ===== 1. Parse YAML to understand structure =====
config = yaml.safe_load(raw)

# Show current providers and custom_providers structure
print("=== Current providers ===")
print(config.get("providers", {}))
print("\n=== Current custom_providers ===")
for cp in config.get("custom_providers", []):
    print(f"  - {cp['name']}: model={cp.get('model','?')}, models_field={'yes' if 'models' in cp else 'no'}")

# ===== 2. Update custom_providers with models lists =====

# Cloudflare curated list (chat generation only, keep it tight)
cloudflare_models = [
    "@cf/moonshotai/kimi-k2.7-code",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/openai/gpt-oss-120b",
    "@cf/qwen/qwen3-30b-a3b-fp8",
    "@cf/qwen/qwq-32b",
    "@cf/qwen/qwen2.5-coder-32b-instruct",
    "@cf/zai-org/glm-5.2",
    "@cf/nvidia/nemotron-3-120b-a12b",
    "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    "@cf/meta/llama-3.1-8b-instruct-fp8",
]

# GitHub Models curated list
github_models = [
    "gpt-4o-mini",
    "gpt-4o",
    "Meta-Llama-3.1-405B-Instruct",
]

# Direct text manipulation for YAML to preserve formatting
import re

# Find Cloudflare block and add models list after model: line
cf_pattern = r"(  - name: Cloudflare Workers AI\s+.*?api_key: [^\n]+\s+.*?base_url: [^\n]+\s+.*?model: '@cf/moonshotai/kimi-k2\.7-code')"
cf_replacement = r"\1\n" + "\n".join(f"    - {m}" for m in ["  models:"] + [f"'{m}'" if ':' in m else m for m in cloudflare_models])

# Actually simpler: just add models after the model line in CF section
old_cf = "  model: '@cf/moonshotai/kimi-k2.7-code'"
new_cf_models = "\n".join(f"    - '{m}'" for m in cloudflare_models)
new_cf = old_cf + "\n  models:\n" + new_cf_models

if old_cf in raw:
    raw = raw.replace(old_cf, new_cf, 1)
    print("\n✅ Added models list to Cloudflare Workers AI")
else:
    print("\n❌ Cloudflare model line not found!")

# GitHub Models - find and update
old_gh = "  model: gpt-4o-mini"
new_gh_models = "\n".join(f"    - {m}" for m in github_models)
new_gh = old_gh + "\n  models:\n" + new_gh_models

# Need to be careful to only replace in GitHub Models context
lines = raw.split("\n")
for i, line in enumerate(lines):
    if "name: GitHub Models" in line:
        for j in range(i, min(i+5, len(lines))):
            if lines[j].strip() == "model: gpt-4o-mini":
                lines[j] = lines[j] + "\n  models:\n" + "\n".join(f"    - {m}" for m in github_models)
                raw = "\n".join(lines)
                print("✅ Added models list to GitHub Models")
                break
        break
else:
    print("❌ GitHub Models block not found!")

# ===== 3. Update providers: section =====
# Add Cloudflare as a named provider so /model picker shows it
# The providers: section structure is:
# providers:
#   cloudflare:
#     api: https://api.cloudflare.com/client/v4/accounts/.../ai/v1
#     models:
#       - @cf/moonshotai/kimi-k2.7-code
#       - ...
#     name: Cloudflare Workers AI

# Check if cloudflare is already in providers
if "cloudflare" not in config.get("providers", {}):
    cf_provider_block = """providers:
  cloudflare:
    api: https://api.cloudflare.com/client/v4/accounts/83398e0c965426307de219b63f7b1ec4/ai/v1
    models:
      - '@cf/moonshotai/kimi-k2.7-code'
      - '@cf/meta/llama-3.3-70b-instruct-fp8-fast'
      - '@cf/openai/gpt-oss-120b'
      - '@cf/qwen/qwen3-30b-a3b-fp8'
      - '@cf/qwen/qwq-32b'
      - '@cf/qwen/qwen2.5-coder-32b-instruct'
      - '@cf/zai-org/glm-5.2'
      - '@cf/nvidia/nemotron-3-120b-a12b'
      - '@cf/deepseek-ai/deepseek-r1-distill-qwen-32b'
      - '@cf/meta/llama-3.1-8b-instruct-fp8'
    name: Cloudflare Workers AI
    request_timeout_seconds: 120
"""
    # Replace the existing providers: block
    # Find where providers: starts and replace up to fallback_providers:
    provider_start = raw.find("providers:\n")
    fallback_start = raw.find("fallback_providers:")
    if provider_start >= 0 and fallback_start > provider_start:
        old_providers_block = raw[provider_start:fallback_start]
        raw = raw.replace(old_providers_block, cf_provider_block + "\n", 1)
        print("✅ Added Cloudflare to providers: section")
    else:
        print("❌ Could not find providers: section boundaries")
else:
    print("ℹ️ Cloudflare already in providers section, skipping")

# Validate final YAML
try:
    validated = yaml.safe_load(raw)
    print("\n✅ Final YAML validation passed!")
except yaml.YAMLError as e:
    print(f"\n❌ YAML validation FAILED: {e}")

# Write back
with open("/home/nsh1l/.hermes/config.yaml", "w") as f:
    f.write(raw)

print("\nDone! Showing updated providers section:")
# Show the updated area
lines = raw.split("\n")
in_providers = False
for i, line in enumerate(lines):
    if line.strip() == "providers:":
        in_providers = True
    if in_providers:
        print(line)
        if line.strip() == "fallback_providers: []":
            break
