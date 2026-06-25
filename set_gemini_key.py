#!/usr/bin/env python3
"""Replace GOOGLE_API_KEY and GEMINI_API_KEY lines in .env.

NOTE: Set GOOGLE_API_KEY environment variable before running.
"""
import re
import os

# Get API key from environment
KEY = os.environ.get("GOOGLE_API_KEY")
if not KEY:
    print("ERROR: GOOGLE_API_KEY environment variable not set")
    print("Usage: export GOOGLE_API_KEY=your_key_here && python3 set_gemini_key.py")
    exit(1)

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
ENV_PATH = os.path.join(HERMES_HOME, ".env")

with open(ENV_PATH) as f:
    content = f.read()

# Replace the commented-out lines
content = re.sub(
    r"^# GOOGLE_API_KEY=your_g\...here$",
    f"GOOGLE_API_KEY={KEY}",
    content,
    flags=re.MULTILINE
)
content = re.sub(
    r"^# GEMINI_API_KEY=your_g\...here  # alias for GOOGLE_API_KEY$",
    f"GEMINI_API_KEY={KEY}  # alias for GOOGLE_API_KEY",
    content,
    flags=re.MULTILINE
)

with open("/home/nsh1l/.hermes/.env", "w") as f:
    f.write(content)

print("✅ Gemini keys set!")
