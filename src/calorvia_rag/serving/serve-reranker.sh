cd ~/vllm_server
source .venv/bin/activate
vllm -v   # vérifier la version

vllm serve /home/nicolas/models/rag/reranker/bge-reranker-v2-m3 \
    --served-model-name bge-reranker-v2-m3 \
    --gpu-memory-utilization 0.1 \
    --max-model-len 4096  \
    --host 0.0.0.0 --port 8002
