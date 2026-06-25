# News OCR Pipeline - AI Assistant Guide

## プロジェクト概要

新聞 PDF → OCR → 埋め込み → Obsidian Vault 知識化パイプライン

**言語**: Python  
**主要技術**: EasyOCR, pdfplumber, sentence-transformers

## ビルドコマンド

```bash
# 依存関係インストール
pip install -r requirements.txt

# 基本的な使用法
python3 obsidian_news_pipeline.py /path/to/newspaper.pdf

# 開発用サーバー起動
python3 upload_server.py
```

## ファイル構造

```
news-ocr-pipeline/
├── obsidian_news_pipeline.py  # メインパイプライン
├── generate_embeddings.py     # 埋め込み生成
├── semantic_search.py         # 意味検索
├── upload_server.py           # HTTPSアップロードサーバー
├── batch_marker.sh           # 一括変換スクリプト
└── config設定スクリプト群/
```

## 主要機能

- PDF → 画像変換（pdfimages/pdfplumber）
- EasyOCR による日本語・英語 OCR
- 記事の自動検出と分割
- 埋め込み生成（multilingual-e5-small）
- 既存ノートとの類似度計算
- Obsidian 用 Markdown 出力

## 環境変数

```bash
# .env.github
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# .hermes/.env
GOOGLE_API_KEY=your_key_here
CLOUDFLARE_API_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
```

## 注意事項

- EasyOCR には GPU サポートが推奨
- 設定スクリプトには環境固有のシークレットが含まれる可能性
- `venv/`, `__pycache__/`, `vault-ai/embeddings.json` は除外済み