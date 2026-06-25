#!/usr/bin/env python3
"""Apply ALL recommended config improvements."""
import os

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")

with open(CONFIG_PATH) as f:
    content = f.read()

changes = []

# 1. Fallback Model — uncomment
if "# fallback_model:" in content:
    content = content.replace(
        "# fallback_model:\n#   provider: openrouter\n#   model: anthropic/claude-sonnet-4",
        "fallback_model:\n  provider: openrouter\n  model: anthropic/claude-sonnet-4"
    )
    changes.append("1. Fallback Model — OpenRouter (Claude Sonnet 4)")

# 2. TTS: openai → edge (free!)
content = content.replace(
    "  provider: openai\n  edge:",
    "  provider: edge\n  edge:"
)
changes.append("2. TTS → Edge (無料)")

# 3. Approval mode: manual → smart
content = content.replace(
    "  mode: manual\n  timeout: 120",
    "  mode: smart\n  timeout: 120"
)
changes.append("3. Approval mode → smart")

# 4. Timezone → Asia/Tokyo
content = content.replace("timezone: ''", "timezone: Asia/Tokyo")
changes.append("4. Timezone → Asia/Tokyo")

# 5. Session auto-prune → ON
content = content.replace(
    "  auto_prune: false\n  retention_days: 90",
    "  auto_prune: true\n  retention_days: 90"
)
changes.append("5. Session auto-prune → ON")

# 6. Image gen → Cloudflare Workers AI (Flux)
content = content.replace(
    "image_gen:\n  use_gateway: true",
    "image_gen:\n  use_gateway: true\n  provider: custom:Cloudflare Workers AI\n  model: '@cf/black-forest-labs/flux-2-klein-9b'"
)
changes.append("6. Image gen → Cloudflare Workers AI (Flux)")

# 7. Discord timestamps → ON
content = content.replace(
    "  message_timestamps:\n    enabled: false",
    "  message_timestamps:\n    enabled: true"
)
changes.append("7. Discord timestamps → ON")

# 8. Auxiliary compression → OpenRouter (cheap)
content = content.replace(
    "  compression:\n    provider: auto\n    model: ''\n    base_url: ''\n    api_key: ''\n    timeout: 120\n    extra_body: {}",
    "  compression:\n    provider: custom:OpenRouter\n    model: deepseek/deepseek-v4-flash\n    base_url: ''\n    api_key: ''\n    timeout: 120\n    extra_body: {}"
)
changes.append("8. Compression → OpenRouter DeepSeek V4 Flash")

# 9. Auxiliary title_generation → GitHub Models (free)
content = content.replace(
    "  title_generation:\n    provider: auto\n    model: ''\n    base_url: ''\n    api_key: ''\n    timeout: 30\n    extra_body: {}\n    language: ''",
    "  title_generation:\n    provider: custom:GitHub Models\n    model: gpt-4o-mini\n    base_url: ''\n    api_key: ''\n    timeout: 30\n    extra_body: {}\n    language: ''"
)
changes.append("9. Title generation → GitHub Models (無料)")

# 10. Auxiliary skills_hub → GitHub Models (free)
content = content.replace(
    "  skills_hub:\n    provider: auto\n    model: ''\n    base_url: ''\n    api_key: ''\n    timeout: 30\n    extra_body: {}",
    "  skills_hub:\n    provider: custom:GitHub Models\n    model: gpt-4o-mini\n    base_url: ''\n    api_key: ''\n    timeout: 30\n    extra_body: {}"
)
changes.append("10. Skills hub → GitHub Models (無料)")

# 11. Auxiliary web_extract → GitHub Models (free)
content = content.replace(
    "  web_extract:\n    provider: auto\n    model: ''\n    base_url: ''\n    api_key: ''\n    timeout: 360\n    extra_body: {}",
    "  web_extract:\n    provider: custom:GitHub Models\n    model: gpt-4o-mini\n    base_url: ''\n    api_key: ''\n    timeout: 360\n    extra_body: {}"
)
changes.append("11. Web extract → GitHub Models (無料)")

with open("/home/nsh1l/.hermes/config.yaml", "w") as f:
    f.write(content)

print("🎯 All changes applied!\n")
for ch in changes:
    print(f"  {ch}")
print("\n✅ YAML validation...")
