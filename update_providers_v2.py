#!/usr/bin/env python3
"""
Update config.yaml: add curated model lists and add Cloudflare to providers section.
Preserves existing ollama provider.
"""
import re

with open("/home/nsh1l/.hermes/config.yaml", "r") as f:
    raw = f.read()

# ===== 1. Add models list to Cloudflare custom_providers entry =====
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

old_cf = "  model: '@cf/moonshotai/kimi-k2.7-code'"
new_cf_models_block = "\n".join(f"    - '{m}'" for m in cloudflare_models)
new_cf = old_cf + "\n  models:\n" + new_cf_models_block

if old_cf in raw:
    raw = raw.replace(old_cf, new_cf, 1)
    print("✅ Added models list to Cloudflare Workers AI (custom_providers)")
else:
    print("❌ Cloudflare model line not found!")

# ===== 2. Add models list to GitHub Models custom_providers entry =====
github_models = [
    "gpt-4o-mini",
    "gpt-4o",
    "Meta-Llama-3.1-405B-Instruct",
]

lines = raw.split("\n")
for i, line in enumerate(lines):
    if "name: GitHub Models" in line:
        for j in range(i, min(i+5, len(lines))):
            if lines[j].strip() == "model: gpt-4o-mini":
                gh_block = "\n  models:\n" + "\n".join(f"    - {m}" for m in github_models)
                lines[j] = lines[j] + gh_block
                raw = "\n".join(lines)
                print("✅ Added models list to GitHub Models (custom_providers)")
                break
        break
else:
    print("❌ GitHub Models block not found!")

# ===== 3. Add Cloudflare to the providers: section (keep ollama) =====
# Check if cloudflare already in providers
if "cloudflare" not in raw.split("\n")[6:15]:  # only check the providers section area
    cloudflare_entry = """\n  cloudflare:
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
    # Insert after "  name: Ollama" line in the ollama block
    target = "    name: Ollama"
    if target in raw:
        raw = raw.replace(target, target + cloudflare_entry, 1)
        print("✅ Added Cloudflare to providers: section (alongside ollama)")
    else:
        print("❌ Could not find 'name: Ollama' in providers section!")
else:
    print("ℹ️ Cloudflare already in providers section")

# ===== 4. Validate YAML =====
import yaml
try:
    validated = yaml.safe_load(raw)
    print("✅ Final YAML validation passed!")
except yaml.YAMLError as e:
    print(f"❌ YAML validation FAILED: {e}")
    # Show problematic area
    exit(1)

# ===== 5. Write =====
with open("/home/nsh1l/.hermes/config.yaml", "w") as f:
    f.write(raw)

# ===== 6. Show result =====
print("\n=== Updated providers: section ===")
lines = raw.split("\n")
in_providers = False
for i, line in enumerate(lines):
    if line.strip() == "providers:":
        in_providers = True
    if in_providers:
        print(line)
        if line.strip() == "fallback_providers: []":
            break

print("\n=== Updated custom_providers models ===")
in_custom = False
for line in lines:
    if line.strip() == "custom_providers:":
        in_custom = True
    if in_custom:
        if line.strip().startswith("- name:") or line.strip().startswith("models:") or (line.strip().startswith("- '") or line.strip().startswith("- gpt") or line.strip().startswith("- Meta")):
            print(line)
