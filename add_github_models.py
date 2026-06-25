#!/usr/bin/env python3
"""Add curated model lists to GitHub Models in config.yaml"""
import re, yaml, os

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
path = os.path.join(HERMES_HOME, "config.yaml")

with open(path, "r") as f:
    cfg = f.read()

# GitHub Models block: find the exact line and add models: after model:
# Current:
#   model: gpt-4o-mini
#   name: GitHub Models
# Need:
#   model: gpt-4o-mini
#   models:
#   - gpt-4o-mini
#   ...
#   name: GitHub Models

gh_models = """\
  models:  # curated list for /model picker
  - gpt-4o-mini
  - gpt-4o
  - Meta-Llama-3.1-405B-Instruct
  - Meta-Llama-3.1-8B-Instruct
  - text-embedding-3-large
  - text-embedding-3-small"""

old = "  model: gpt-4o-mini\n  name: GitHub Models"
new = f"  model: gpt-4o-mini\n{gh_models}\n  name: GitHub Models"

if old in cfg:
    cfg = cfg.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(cfg)
    
    # Validate
    try:
        parsed = yaml.safe_load(cfg)
        print("✅ YAML validation passed!")
    except yaml.YAMLError as e:
        print(f"❌ YAML validation FAILED: {e}")
        exit(1)
    
    # Verify
    if "models:" in cfg and "GitHub Models" in cfg:
        print("✅ GitHub Models models list added successfully!")
        # Show the changed section
        lines = cfg.split("\n")
        for i, line in enumerate(lines):
            if "api_key: github" in line:
                for j in range(i, i+12):
                    print(f"  {lines[j]}")
                break
else:
    print("❌ Could not find the target old string!")
    print(f"Looking for: {repr(old)}")
    # Debug: find the actual lines
    lines = cfg.split("\n")
    for i, line in enumerate(lines):
        if "gpt-4o-mini" in line and "model:" in line:
            print(f"Found model line {i}: {line}")
            print(f"Next line {i+1}: {lines[i+1]}")
            break
