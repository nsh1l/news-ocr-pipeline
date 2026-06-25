#!/bin/bash
# 新聞PDF一括変換スクリプト (Marker-PDF版)
# --------------------------------------------------
export TMPDIR=/home/nsh1l/tmp-embed
source /home/nsh1l/tmp-embed/marker-venv/bin/activate

INPUT_DIR="/home/nsh1l/news-input"
OUTPUT_DIR="/home/nsh1l/news-output-marker"
LOG_FILE="/home/nsh1l/news-output-marker/batch_process.log"

mkdir -p "$OUTPUT_DIR"
echo "Starting batch processing at $(date)" > "$LOG_FILE"

# PDFファイルを列挙してループ
find "$INPUT_DIR" -name "*.pdf" | while read -r pdf_file; do
    filename=$(basename "$pdf_file")
    echo "--- Processing: $filename ---" | tee -a "$LOG_FILE"
    
    # marker_single で変換
    # --languages ja: 日本語指定
    # --batch_multiplier 1: メモリ節約（Mac Mini用）
    marker_single "$pdf_file" "$OUTPUT_DIR" --languages ja --batch_multiplier 1 >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "Successfully converted: $filename" | tee -a "$LOG_FILE"
    else
        echo "FAILED: $filename" | tee -a "$LOG_FILE"
    fi
done

echo "Batch processing finished at $(date)" | tee -a "$LOG_FILE"
