llama-server -m /home/nicolas/models/gemma4-26b-a4b/llama/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf \
    --alias gemma-4-26b \
    -ngl 99 -fa on \
    --parallel 1 --ctx-size 8196 \
    -ctk q8_0 -ctv q8_0 \
    --model-draft /home/nicolas/models/gemma4-26b-a4b/llama/mtp-gemma-4-26B-A4B-it.gguf \
    --spec-type draft-mtp --spec-draft-n-max 4 \
    --host 0.0.0.0 --port 8000

llama-server \
      -m /home/nicolas/models/qwen3.8-27b/llama/Qwen3.8-27B-UD-Q4_K_XL.gguf \
      -ngl 50 -fa on \
      --parallel 3 --ctx-size 16384 \
      -ctk q8_0 -ctv q8_0 \
      --spec-type draft-mtp --spec-draft-n-max 4 \
      --port 8000
