#!/usr/bin/env python3
"""Add curated model lists to custom_providers in config.yaml"""
import re, os

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")

with open(CONFIG_PATH, "r") as f:
    cfg = f.read()

# ===== Cloudflare Workers AI =====
cloudflare_models = [
    "  models:  # curated list for /model picker",
    "  - '@cf/moonshotai/kimi-k2.7-code'         # code (default)",
    "  - '@cf/meta/llama-3.3-70b-instruct-fp8-fast'  # best general",
    "  - '@cf/qwen/qwen3-30b-a3b-fp8'            # high quality",
    "  - '@cf/qwen/qwen2.5-coder-32b-instruct'   # code",
    "  - '@cf/deepseek-ai/deepseek-r1-distill-qwen-32b'# reasoning",
    "  - '@cf/google/gemma-4-26b-a4b-it'         # gemma 4",
    "  - '@cf/mistralai/mistral-small-3.1-24b-instruct' # mistral",
    "  - '@cf/nvidia/nemotron-3-120b-a12b'       # nemotron",
    "  - '@cf/qwen/qwq-32b'                      # reasoning",
    "  - '@cf/meta/llama-4-scout-17b-16e-instruct'    # MoE latest",
    "  - '@cf/zai-org/glm-5.2'                   # glm latest",
]
cf_block = "\n".join(cloudflare_models)

# Find the Cloudflare entry: "name: Cloudflare Workers AI" followed by a newline
# Insert models: list after the "model: '@cf/moonshotai/kimi-k2.7-code'" line
# Pattern: find the exact line with "model: '@cf/moonshotai/kimi-k2.7-code'"
old_cf_model = "  model: '@cf/moonshotai/kimi-k2.7-code'"
new_cf_model = old_cf_model + "\n" + cf_block
if old_cf_model in cfg:
    cfg = cfg.replace(old_cf_model, new_cf_model, 1)
    print("✅ Added models list to Cloudflare Workers AI")
else:
    print("❌ Cloudflare model line not found!")

# ===== GitHub Models =====
github_models = [
    "  models:  # curated list for /model picker",
    "  - gpt-4o-mini",
    "  - gpt-4o",
    "  - Meta-Llama-3.1-405B-Instruct",
    "  - Meta-Llama-3.1-8B-Instruct",
    "  - text-embedding-3-large",
    "  - text-embedding-3-small",
]
gh_block = "\n".join(github_models)

old_gh_model = "  model: gpt-4o-mini"
new_gh_model = old_gh_model + "\n" + gh_block
# Need to be careful - only replace in the GitHub Models entry
# Find context: look for the specific line after "name: GitHub Models"
lines = cfg.split("\n")
for i, line in enumerate(lines):
    if "name: GitHub Models" in line:
        # The model: gpt-4o-mini line should be a few lines after
        for j in range(i, min(i+5, len(lines))):
            if lines[j].strip() == "model: gpt-4o-mini":
                lines[j] = lines[j] + "\n" + gh_block
                cfg = "\n".join(lines)
                print("✅ Added models list to GitHub Models")
                break
        break
else:
    print("❌ GitHub Models block not found!")

# Write back
with open("/home/nsh1l/.hermes/config.yaml", "w") as f:
    f.write(cfg)

# Validate YAML
import yaml
try:
    parsed = yaml.safe_load(cfg)
    print("✅ YAML validation passed!")
except yaml.YAMLError as e:
    print(f"❌ YAML validation FAILED: {e}")
    exit(1)

# Show the updated custom_providers section
print("\n=== Updated custom_providers ===")
for line in cfg.split("\n"):
    if "custom_providers:" in line and not line.strip().startswith("#"):
        # Print from here
        found = True
if found:
    # Find the section
    lines = cfg.split("\n")
    in_section = False
    for i, line in enumerate(lines):
        if line.strip() == "custom_providers:":
            in_section = True
        if in_section:
            print(line)
            if i > 0 and lines[i-1].strip() == "name: OpenRouter":
                break
