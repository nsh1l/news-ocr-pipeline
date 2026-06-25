# News OCR Pipeline

新聞 PDF → OCR → 埋め込み → Obsidian Vault 知識化パイプライン

## 概要

このプロジェクトは、新聞 PDF ファイルを処理して Obsidian Vault に知識として取り込むためのパイプラインです。EasyOCR を使用してテキストを抽出し、記事ごとに分割し、埋め込みを生成して既存のノートと関連付けます。

## パイプラインアーキテクチャ

```
┌─────────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ 新聞 PDF    │ ──→ │ EasyOCR  │ ──→ │ 記事分割    │ ──→ │ 埋め込み生成  │ ──→ │ Obsidian    │
│             │     │ (JA/EN)  │     │ (自動検出)  │     │ (multilingual│     │ Vault       │
│             │     │          │     │             │     │  -e5-small)  │     │             │
└─────────────┘     └──────────┘     └─────────────┘     └──────────────┘     └─────────────┘
```

## スクリプト一覧

### メインパイプライン

#### `obsidian_news_pipeline.py`
新聞 PDF を処理するメインパイプラインスクリプト。

**機能:**
- PDF → 画像変換（pdfimages/pdfplumber）
- EasyOCR による日本語・英語 OCR
- 記事の自動検出と分割
- 埋め込み生成（multilingual-e5-small）
- 既存ノートとの類似度計算
- Obsidian 用 Markdown 出力

**使用例:**
```bash
python3 obsidian_news_pipeline.py /path/to/news.pdf --date 2026-06-23
python3 obsidian_news_pipeline.py news.pdf --output-dir ./output --vault-path ../vault
```

### 埋め込み・検索

#### `generate_embeddings.py`
Obsidian Vault 内の全ノートを読み込み、埋め込みを生成します。

**出力:**
- `vault-ai/index.json` - ノート一覧
- `vault-ai/metadata.json` - フロントマター・AI 分析
- `vault-ai/embeddings.json` - 埋め込みベクトル
- `vault-ai/summary.json` - 統計情報

**使用例:**
```bash
python3 generate_embeddings.py --vault-path ../vault --output ./vault-ai
```

#### `semantic_search.py`
意味検索による Vault 内ノート検索。

**使用例:**
```bash
python3 semantic_search.py "検索クエリ" --top-k 10 --verbose
python3 semantic_search.py "AI" --type daily --json
```

### 設定ユーティリティ

#### `fetch_models.py`
全プロバイダーの最新モデル一覧を取得。

**対応プロバイダー:**
- Google Gemini
- OpenRouter（$5/M トークン未満）
- GitHub Models（無料）
- Cloudflare Workers AI
- カスタムプロバイダー

**使用例:**
```bash
python3 fetch_models.py
```

#### `add_github_models.py`
GitHub Models のモデル一覧を config.yaml に追加。

#### `add_mcp_servers.py`
MCP サーバー設定を config.yaml に追加。

**追加サーバー:**
- time - 時刻・タイムゾーン
- filesystem - ファイルシステムアクセス
- brave-search - Brave Search
- github - GitHub API
- fetch - HTML→Markdown 変換

#### `add_models_lists.py`
Cloudflare Workers AI と GitHub Models のモデル一覧を追加。

#### `patch_config.py` / `patch_config_v2.py`
config.yaml の設定をパッチ適用。

**注意:** これらのスクリプトは環境固有の設定を含みます。使用前に内容を確認してください。

#### `set_gemini_key.py`
Google Gemini API キーを設定。

#### `inject_github_token.py`
GitHub トークンを MCP サーバー設定に注入。

## セットアップ

### 必要なパッケージ

```bash
pip install easyocr pdfplumber pillow sentence-transformers
pip install numpy
```

### 環境変数

以下の環境変数を設定してください：

```bash
# .env.github
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# .hermes/.env
GOOGLE_API_KEY=your_key_here
CLOUDFLARE_API_TOKEN=your_token_here
OPENROUTER_API_KEY=your_key_here
```

### 依存ライブラリ

- **EasyOCR**: 日本語・英語 OCR
- **pdfplumber**: PDF 処理
- **sentence-transformers**: 埋め込み生成
- **Pillow**: 画像処理

## 使用方法

### 1. 新聞 PDF の処理

```bash
# 基本的な使用法
python3 obsidian_news_pipeline.py /path/to/newspaper.pdf

# 日付指定
python3 obsidian_news_pipeline.py news.pdf --date 2026-06-23

# 出力ディレクトリ指定
python3 obsidian_news_pipeline.py news.pdf --output-dir ./my-notes

# Vault パス指定（類似検索用）
python3 obsidian_news_pipeline.py news.pdf --vault-path /path/to/vault
```

### 2. 埋め込み生成

```bash
# Vault 全体の埋め込みを生成
python3 generate_embeddings.py --vault-path /path/to/vault
```

### 3. 意味検索

```bash
# 基本検索
python3 semantic_search.py "機械学習"

# 詳細出力
python3 semantic_search.py "AI" --top-k 10 --verbose

# JSON 出力
python3 semantic_search.py "テスト" --json
```

## 出力形式

生成される Markdown ファイルは以下の形式です：

```markdown
---
type: newspaper
created: 2026-06-23T00:00:00
source: newspaper.pdf (page 1)
themes: [newspaper]
---

# 記事タイトル

記事本文...

## 関連ノート
- [[ノート名]] (sim: 0.85)
- [[別のノート]] (sim: 0.72)

<!-- source: newspaper.pdf page 1 -->
```

## 注意事項

- **秘密情報の管理**: `patch_config.py` や `set_gemini_key.py` には環境固有のシークレットが含まれる可能性があります。これらを公開リポジトリにコミットする前に、必ず環境変数参照に置き換えてください。
- **仮想環境**: `venv/` ディレクトリは.gitignore に含まれています。
- **キャッシュ**: `__pycache__/` や `vault-ai/embeddings.json` も除外されています。

## ライセンス

MIT
