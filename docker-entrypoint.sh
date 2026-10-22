#!/bin/sh
set -e

# ==============================================================================
# Smart Contract Analyser - Backend Docker Entrypoint
# ==============================================================================
MODEL_DIR="analysis/models/legal_bert_v3.3.0"
WEIGHTS_FILE="$MODEL_DIR/model.safetensors"

mkdir -p "$MODEL_DIR"

if [ ! -f "$WEIGHTS_FILE" ] && [ ! -f "$MODEL_DIR/pytorch_model.bin" ]; then
    echo "[SCA-INIT] Legal-BERT checkpoint weights not found at $WEIGHTS_FILE"
    
    # Method A: Download pre-trained weights from external release/storage URL if provided
    if [ -n "$MODEL_WEIGHTS_URL" ]; then
        echo "[SCA-INIT] Downloading model weights from $MODEL_WEIGHTS_URL..."
        curl -f -L -o "$WEIGHTS_FILE" "$MODEL_WEIGHTS_URL"
        echo "[SCA-INIT] Model weights successfully downloaded."
    # Method B: Auto-train from canonical frozen dataset if explicitly requested
    elif [ "$AUTO_TRAIN_ON_STARTUP" = "1" ] || [ "$AUTO_TRAIN_ON_STARTUP" = "true" ]; then
        echo "[SCA-INIT] AUTO_TRAIN_ON_STARTUP is enabled. Training Legal-BERT from canonical dataset..."
        python -m analysis.train_legal_bert --output-dir "$MODEL_DIR" --force
        echo "[SCA-INIT] Training completed successfully."
    else
        echo "[SCA-INIT] NOTE: Model weights are absent. The backend will start in diagnostic standby mode."
        echo "[SCA-INIT] The /ready endpoint will report HTTP 503 until model.safetensors is mounted or supplied."
    fi
else
    echo "[SCA-INIT] Verified Legal-BERT checkpoint weights at $MODEL_DIR"
fi

echo "[SCA-INIT] Launching Uvicorn single-worker process for in-memory job coordination..."
exec uvicorn analysis.api:app --host 0.0.0.0 --port 8000 --workers 1
