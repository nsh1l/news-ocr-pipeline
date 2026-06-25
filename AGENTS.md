# AGENTS.md - News OCR Pipeline

## プロジェクト概要
新聞 PDF を OCR でテキスト化し、埋め込みベクトルを生成して Obsidian Vault に知識として取り込むパイプライン。

## 技術スタック
- Python 3.13
- EasyOCR（日本語・英語 OCR）
- sentence-transformers（multilingual-e5-small）
- pdfplumber（PDF 処理）

## ビルド・実行コマンド
```bash
# パイプライン実行
python3 obsidian_news_pipeline.py /path/to/news.pdf --date 2026-06-23

# 埋め込み生成
python3 generate_embeddings.py --vault-path /path/to/vault

# 意味検索
python3 semantic_search.py "検索クエリ" --top-k 10
```

## ファイル構造
- `obsidian_news_pipeline.py` - メインパイプライン
- `generate_embeddings.py` - 埋め込み生成
- `semantic_search.py` - 意味検索
- `fetch_models.py` - モデル一覧取得
- `upload_server.py` - HTTPS アップロードサーバー
- `batch_marker.sh` - PDF 一括変換

## コードスタイル
- ruff 使用（ruff.toml 参照）
- 行長：120 文字
- インデント：スペース 4 個