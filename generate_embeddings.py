#!/usr/bin/env python3
"""
Cognitive Vault AI - Embedding Generator
Scans Obsidian vault, extracts frontmatter + content, generates embeddings
using sentence-transformers, and writes structured output.

Usage:
    python3 scripts/generate_embeddings.py [--vault-path ../vault] [--output ../vault-ai]
"""

import argparse
import json
import os
import sys
import re
import hashlib
from pathlib import Path
from datetime import datetime


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a markdown file."""
    frontmatter = {}
    body = content
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        body = match.group(2).strip()
        for line in yaml_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, _, val = line.partition(':')
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val == '' or val == '[]':
                    frontmatter[key] = None
                elif val.startswith('[') and val.endswith(']'):
                    items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(',') if v.strip()]
                    frontmatter[key] = items
                else:
                    frontmatter[key] = val
    return frontmatter, body


def extract_ai_analysis(content: str) -> dict:
    """Extract AI-analyzed fields (themes, emotion, decision_patterns, related_notes)."""
    analysis = {"themes": [], "emotion": [], "decision_patterns": [], "related_notes": []}
    current_key = None
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('- '):
            val = stripped[2:].strip()
            if current_key in analysis:
                analysis[current_key].append(val)
        elif stripped.endswith(':') and stripped[:-1] in analysis:
            current_key = stripped[:-1]
        else:
            for key in analysis:
                m = re.match(rf'^{key}:\s*(.+)$', stripped, re.IGNORECASE)
                if m:
                    val = m.group(1).strip().strip('"').strip("'")
                    if val:
                        analysis[key].append(val)
    return analysis


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]


def scan_vault(vault_path: Path) -> list[dict]:
    """Scan the vault directory and collect all markdown files with metadata."""
    notes = []
    for md_file in sorted(vault_path.rglob('*.md')):
        if 'templates' in md_file.parts:
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"  ⚠ Skipping {md_file}: {e}", file=sys.stderr)
            continue
        frontmatter, body = parse_frontmatter(content)
        rel_path = md_file.relative_to(vault_path)
        ai_analysis = extract_ai_analysis(content)
        notes.append({
            "path": str(rel_path),
            "frontmatter": frontmatter,
            "body_preview": body[:500],
            "body_length": len(body),
            "content_hash": compute_content_hash(body),
            "ai_analysis": ai_analysis,
            "last_modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
        })
        print(f"  ✓ {rel_path}", file=sys.stderr)
    return notes


def generate_embeddings(notes: list[dict]) -> list[list[float]]:
    """Generate embeddings using sentence-transformers."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.", file=sys.stderr)
        print("Run: pip install sentence-transformers", file=sys.stderr)
        sys.exit(1)
    print(f"\nLoading multilingual-e5-small...", file=sys.stderr)
    model = SentenceTransformer('intfloat/multilingual-e5-small')
    print(f"Model loaded. Generating embeddings...", file=sys.stderr)
    texts = [f"[{note.get('frontmatter', {}).get('type', 'note')}] {note['body_preview']}" for note in notes]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True, batch_size=32)
    print(f"Generated {len(embeddings)} embeddings, dim={embeddings.shape[1]}", file=sys.stderr)
    return embeddings.tolist()


def write_outputs(notes: list[dict], embeddings: list[list[float]], output_path: Path):
    """Write index.json, metadata.json, embeddings.json, and summary.json."""
    output_path.mkdir(parents=True, exist_ok=True)
    # index.json
    index = [{"path": n["path"], "type": n.get("frontmatter", {}).get("type", "note"),
              "created": n.get("frontmatter", {}).get("created", ""),
              "title": n["path"].replace('.md', '').replace('/', ' / '),
              "body_preview": n["body_preview"][:200], "content_hash": n["content_hash"]} for n in notes]
    (output_path / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  ✓ {output_path / 'index.json'} ({len(index)} entries)", file=sys.stderr)
    # metadata.json
    metadata = [{"path": n["path"], "frontmatter": n["frontmatter"], "body_length": n["body_length"],
                 "content_hash": n["content_hash"], "ai_analysis": n["ai_analysis"],
                 "last_modified": n["last_modified"]} for n in notes]
    (output_path / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  ✓ {output_path / 'metadata.json'}", file=sys.stderr)
    # embeddings.json
    emb_dict = {n["path"]: emb for n, emb in zip(notes, embeddings)}
    (output_path / "embeddings.json").write_text(json.dumps(emb_dict, ensure_ascii=False), encoding='utf-8')
    print(f"  ✓ {output_path / 'embeddings.json'} ({len(emb_dict)} vectors)", file=sys.stderr)
    # summary.json
    note_types = {}
    for n in notes:
        nt = n.get("frontmatter", {}).get("type", "unknown")
        note_types[nt] = note_types.get(nt, 0) + 1
    summary = {"generated_at": datetime.now().isoformat(), "total_notes": len(notes),
               "embedding_model": "intfloat/multilingual-e5-small",
               "embedding_dim": len(embeddings[0]) if embeddings else 0, "note_types": note_types}
    (output_path / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  ✓ {output_path / 'summary.json'}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for Cognitive Vault")
    parser.add_argument("--vault-path", type=str,
                        default=os.path.join(os.path.dirname(__file__), "..", "vault"))
    parser.add_argument("--output", type=str,
                        default=os.path.join(os.path.dirname(__file__), "..", "vault-ai"))
    args = parser.parse_args()
    vault_path = Path(args.vault_path).resolve()
    output_path = Path(args.output).resolve()
    if not vault_path.exists():
        print(f"ERROR: Vault path not found: {vault_path}", file=sys.stderr)
        sys.exit(1)
    print(f"🔍 Scanning vault: {vault_path}", file=sys.stderr)
    notes = scan_vault(vault_path)
    if not notes:
        print("No markdown files found.", file=sys.stderr)
        return
    print(f"\n📝 Found {len(notes)} markdown files", file=sys.stderr)
    print(f"\n🧠 Generating embeddings...", file=sys.stderr)
    embeddings = generate_embeddings(notes)
    print(f"\n💾 Writing output to: {output_path}", file=sys.stderr)
    write_outputs(notes, embeddings, output_path)
    print(f"\n✅ Done! {len(notes)} notes indexed.", file=sys.stderr)


if __name__ == "__main__":
    main()
