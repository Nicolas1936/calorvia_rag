cd ~/vllm_server
source .venv/bin/activate
vllm -v   # vérifier la version

vllm serve /home/nicolas/models/rag/embedder/bge-m3 \
    --served-model-name bge-m3 \
    --gpu-memory-utilization 0.1 \
    --max-model-len 8192 \
    --host 0.0.0.0 --port 8001
