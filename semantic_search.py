#!/usr/bin/env python3
"""
Cognitive Vault AI - Semantic Search
Search vault notes by meaning using cosine similarity on embeddings.

Usage:
    python3 scripts/semantic_search.py "検索クエリ"
    python3 scripts/semantic_search.py "検索クエリ" --top-k 10 --type daily --verbose
"""

import argparse
import json
import os
import sys
import math
from pathlib import Path


def load_embeddings(vault_ai_path: Path):
    emb_path = vault_ai_path / "embeddings.json"
    idx_path = vault_ai_path / "index.json"
    meta_path = vault_ai_path / "metadata.json"
    if not emb_path.exists():
        print(f"ERROR: embeddings.json not found at {emb_path}", file=sys.stderr)
        print("Run scripts/generate_embeddings.py first.", file=sys.stderr)
        sys.exit(1)
    with open(emb_path, encoding='utf-8') as f:
        embeddings = json.load(f)
    index = []
    if idx_path.exists():
        with open(idx_path, encoding='utf-8') as f:
            index = json.load(f)
    metadata = {}
    if meta_path.exists():
        with open(meta_path, encoding='utf-8') as f:
            for m in json.load(f):
                metadata[m["path"]] = m
    return embeddings, index, metadata


def generate_query_embedding(query: str) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.", file=sys.stderr)
        sys.exit(1)
    model = SentenceTransformer('intfloat/multilingual-e5-small')
    emb = model.encode(query, normalize_embeddings=True)
    return emb.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def search(query: str, embeddings: dict, index: list, metadata: dict,
           top_k: int = 5, note_type: str | None = None) -> list[dict]:
    query_emb = generate_query_embedding(query)
    valid_paths = {item["path"] for item in index if item.get("type") == note_type} if note_type else set(embeddings.keys())
    results = []
    for path, emb in embeddings.items():
        if path not in valid_paths:
            continue
        score = cosine_similarity(query_emb, emb)
        results.append({"path": path, "score": round(score, 4)})
    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:top_k]
    for r in top:
        r["type"] = ""
        r["body_preview"] = ""
        r["frontmatter"] = {}
        r["ai_analysis"] = {}
        for item in index:
            if item["path"] == r["path"]:
                r["type"] = item.get("type", "")
                r["body_preview"] = item.get("body_preview", "")
                break
        if r["path"] in metadata:
            r["frontmatter"] = metadata[r["path"]].get("frontmatter", {})
            r["ai_analysis"] = metadata[r["path"]].get("ai_analysis", {})
    return top


def main():
    parser = argparse.ArgumentParser(description="Semantic search in Cognitive Vault")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--vault-ai", type=str, default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--type", type=str, default=None,
                        choices=["daily", "failure", "decision", "observation", "note"])
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    vault_ai_path = Path(args.vault_ai).resolve() if args.vault_ai else Path(os.path.dirname(__file__)).parent / "vault-ai"
    if not vault_ai_path.exists():
        print(f"ERROR: vault-ai directory not found: {vault_ai_path}", file=sys.stderr)
        sys.exit(1)
    embeddings, index, metadata = load_embeddings(vault_ai_path)
    results = search(args.query, embeddings, index, metadata, top_k=args.top_k, note_type=args.type)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results found.")
            return
        print(f"\nTop {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            score_bar = "█" * int(r["score"] * 20) + "░" * (20 - int(r["score"] * 20))
            print(f"  [{i}] [{score_bar}] {r['score']*100:.1f}%  |  {r['path']}")
            if args.verbose:
                preview = r.get("body_preview", "")[:200]
                if preview:
                    print(f"       {preview}")
                ai = r.get("ai_analysis", {})
                if ai.get("themes"):
                    print(f"       📂 Themes: {', '.join(ai['themes'])}")
                if ai.get("emotion"):
                    print(f"       😊 Emotion: {', '.join(ai['emotion'])}")
                if ai.get("decision_patterns"):
                    print(f"       🧠 Patterns: {', '.join(ai['decision_patterns'])}")
            print()


if __name__ == "__main__":
    main()
