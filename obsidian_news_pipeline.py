#!/usr/bin/env python3
"""
新聞PDF → Obsidian Vault 知識化パイプライン

Usage:
    python3 obsidian_news_pipeline.py /path/to/news.pdf --date 2026-06-23
"""

import os
import sys
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime

# OCR
import easyocr
# PDF → Image
import pdfplumber
from PIL import Image
import io

# Embedding
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
VAULT_AI_DIR = Path(__file__).parent / "vault-ai"
OUTPUT_MARKDOWN_DIR = Path(__file__).parent  # markdown notes go here

# Embedding model (384-dim, multilingual-e5-small)
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# EasyOCR languages
EASYOCR_LANGS = ["ja", "en"]


def pdf_pages_to_images(pdf_path: str) -> list[Image.Image]:
    """
    PDF → list of PIL Images.
    Strategy:
      1. Try pdfimages (poppler) for lossless JPEG extraction (best for scanned PDFs)
      2. Fallback to pdfplumber
    """
    import subprocess
    import tempfile as tf
    import shutil

    # 1. Try pdfimages first (lossless extraction from scanned PDFs)
    tmpdir = tf.mkdtemp(prefix="pdfpages_")
    try:
        pdfimages_path = shutil.which("pdfimages")
        if pdfimages_path:
            # -j: save as JPEG, -l: all pages
            result = subprocess.run(
                [pdfimages_path, "-j", "-l", "1", pdf_path, f"{tmpdir}/page"],
                capture_output=True, text=True
            )
            imgs = sorted(Path(tmpdir).glob("page-*.jpg"))
            if imgs:
                images = [Image.open(str(p)) for p in imgs]
                print(f"    → pdfimages extracted {len(images)} page(s) (lossless)")
                return images
    except Exception as e:
        print(f"    pdfimages fallback: {e}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # 2. Fallback: pdfplumber (may be lower quality for scanned PDFs)
    images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pil_img = page.to_image(resolution=200).original
            # Handle both numpy array and PIL Image
            if isinstance(pil_img, Image.Image):
                images.append(pil_img.convert("RGB"))
            else:
                # Assume numpy array
                import numpy as np
                images.append(Image.fromarray(np.array(pil_img)))
    return images


def ocr_image(reader, img: Image.Image) -> str:
    """
    EasyOCR → extracted text.
    Applies grayscale + contrast enhancement for newspaper scans.
    """
    import numpy as np
    from PIL import ImageEnhance

    # Convert to grayscale and enhance for better OCR on scanned newspapers
    gray = img.convert("L")
    enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)

    # Convert back to RGB for EasyOCR
    img_processed = enhanced.convert("RGB")
    img_np = np.array(img_processed)

    result = reader.readtext(img_np, detail=0, paragraph=False)
    return "\n".join(result)


def split_into_articles(text: str) -> list[dict]:
    """
    Split newspaper text into articles.
    Strategy: split on common article-boundary markers:
      - lines starting with category names (カタカナ3文字以上 or 特定キーワード)
      - double newlines followed by uppercase/カタカナ
    Returns list of {"title": str, "body": str}
    """
    import re
    lines = text.split("\n")
    articles = []
    current_title = " ARTICLE "
    current_lines = []
    
    # Article boundary regex: category-like header
    TITLE_PATTERN = re.compile(r"^《([^》]+)》|^【([^】]+)】|^([A-ZА-ЯА-Яa-z]{3,})[：:]?\s*|^《([^\s]{2,4})》")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                current_lines.append("")
            continue
        
        # Detect new article header
        is_header = bool(TITLE_PATTERN.search(stripped)) or (
            len(stripped) < 30 and
            (stripped.isupper() or re.match(r"^[А-ЯA-Z]+", stripped) or "《" in stripped or "【" in stripped)
        )
        
        if is_header and current_lines:
            # Save previous article
            body = "\n".join(current_lines).strip()
            if body:
                articles.append({"title": current_title.strip(), "body": body})
            current_title = stripped
            current_lines = []
        else:
            current_lines.append(stripped)
    
    # Last article
    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            articles.append({"title": current_title.strip(), "body": body})
    
    return articles


def load_embedding_model():
    model_path = Path.home() / ".cache" / "sentence_transformers" / "intfloat--multilingual-e5-small"
    return SentenceTransformer(str(model_path)) if model_path.exists() else SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(model, texts: list[str]) -> list:
    """Generate normalized embeddings"""
    return [model.encode(t, normalize_embeddings=True) for t in texts]


def find_related_notes(article_embedding, vault_embeddings_path: Path, top_k: int = 5) -> list[dict]:
    """Find related notes from vault-ai embeddings"""
    import numpy as np
    emb_file = vault_embeddings_path / "embeddings.json"
    idx_file = vault_embeddings_path / "index.json"
    if not emb_file.exists() or not idx_file.exists():
        return []
    
    with open(vault_embeddings_path / "embeddings.json") as f:
        emb_data = json.load(f)
    with open(vault_embeddings_path / "index.json") as f:
        idx_data = json.load(f)
    
    note_paths = [e["path"] for e in idx_data]
    note_vectors = np.array([emb_data[p] for p in note_paths])
    # Ensure 2D shape (N, dim)
    if note_vectors.ndim == 1:
        note_vectors = note_vectors.reshape(-1, 1)
    note_norms = np.linalg.norm(note_vectors, axis=1, keepdims=True)
    note_norms[note_norms == 0] = 1
    note_vectors_norm = note_vectors / note_norms

    article_emb = np.array(article_embedding).flatten()
    sims = note_vectors_norm @ article_emb.reshape(-1, 1)
    top_idx = np.argsort(sims.flatten())[::-1][:top_k]
    
    results = []
    for idx in top_idx:
        if sims[idx] > 0.4:  # threshold
            results.append({
                "note": note_paths[idx],
                "similarity": round(float(sims[idx]), 4)
            })
    return results


def article_to_markdown(article: dict, source_file: str, page_num: int, related: list[dict], news_date: str) -> str:
    """Convert article dict to Obsidian markdown"""
    lines = [
        "---",
        f"type: newspaper",
        f"created: {news_date}T00:00:00",
        f"source: {source_file} (page {page_num})",
        f"themes: [newspaper]",
        "---",
        "",
        f"# {article['title']}",
        "",
        article["body"],
        "",
    ]
    
    if related:
        lines.append("## 関連ノート")
        lines.append("")
        for r in related:
            note_name = Path(r["note"]).stem
            lines.append(f"- [[{note_name}]] (sim: {r['similarity']:.2f})")
        lines.append("")
    
    lines.append(f"<!-- source: {source_file} page {page_num} -->")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Newspaper PDF → Obsidian Knowledge Pipeline")
    parser.add_argument("pdf", help="Path to newspaper PDF")
    parser.add_argument("--date", default=None, help="News date YYYY-MM-DD (default: today)")
    parser.add_argument("--output-dir", default=None, help="Output dir for markdown files")
    parser.add_argument("--vault-path", default=None, help="Vault path for similarity search")
    args = parser.parse_args()

    news_date = args.date or datetime.now().strftime("%Y-%m-%d")
    output_dir = Path(args.output_dir) if args.output_dir else Path.home() / "news-output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    vault_ai = Path(args.vault_path) / "vault-ai" if args.vault_path else VAULT_AI_DIR

    print(f"📰 Processing: {args.pdf}")
    print(f"📅 Date: {news_date}")

    # 1. PDF → Images
    print("  📄 Converting PDF pages to images...")
    try:
        images = pdf_pages_to_images(args.pdf)
        print(f"  → {len(images)} pages")
    except Exception as e:
        print(f"  ⚠️  pdfplumber failed: {e}")
        print("  🔄 Trying pdf2image...")
        from pdf2image import convert_from_path
        images = convert_from_path(args.pdf, dpi=200)
        print(f"  → {len(images)} pages")

    # 2. Initialize EasyOCR
    print("  🔤 Loading EasyOCR model...")
    reader = easyocr.Reader(EASYOCR_LANGS, gpu=False, verbose=False)
    
    # 3. Initialize embedding model
    print("  🧠 Loading embedding model...")
    emb_model = load_embedding_model()
    
    # 4. Process each page
    all_articles = []
    for page_num, img in enumerate(images, 1):
        print(f"  📃 Page {page_num}: OCR...")
        text = ocr_image(reader, img)
        articles = split_into_articles(text)
        
        for article in articles:
            article["page"] = page_num
            # Embed article body
            body_short = article["body"][:500]  # truncate for speed
            emb = emb_model.encode(body_short, normalize_embeddings=True)
            article["embedding"] = emb
            all_articles.append(article)
        
        print(f"    → {len(articles)} articles found")

    print(f"\n  Total articles: {len(all_articles)}")

    # 5. Save each article as markdown
    print("\n  📝 Saving articles to Obsidian notes...")
    saved = []
    for i, article in enumerate(all_articles, 1):
        # Find related notes
        related = find_related_notes(article["embedding"], vault_ai) if vault_ai.exists() else []
        
        # Create filename
        title_clean = article["title"].strip().replace("/", "-").replace("\\", "-")[:40]
        filename = f"{news_date}_{i:02d}_{title_clean}.md"
        filepath = output_dir / filename
        
        md_content = article_to_markdown(article, args.pdf, article["page"], related, news_date)
        filepath.write_text(md_content, encoding="utf-8")
        saved.append(str(filepath))
        print(f"    [{i}] {article['title'][:40]} → {filepath.name}")
        if related:
            for r in related[:2]:
                print(f"         ↔ {Path(r['note']).stem} ({r['similarity']:.2f})")

    print(f"\n✅ Done! {len(saved)} notes saved to {output_dir}")
    print("   Copy these to your Obsidian vault and push to git!")


if __name__ == "__main__":
    main()
