cd ~/vllm_server
source .venv/bin/activate
vllm -v   # vérifier la version

vllm serve /home/nicolas/models/rag/embedder/harrier-oss-v1-0.6b \
    --runner pooling \
    --served-model-name harrier-oss-v1-0.6b \
    --gpu-memory-utilization 0.1 \
    --max-model-len 4096 \
    --port 8001
