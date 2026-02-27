# FAISS MCP (CPU/GPU Embedding) - README

- Purpose: lightweight FAISS-based MCP server that computes sentence-transformer embeddings on CPU (default) or NVIDIA GPU (with CUDA) and exposes MCP tools to add/search/save a local knowledge store.

- Path: `mcp/acknowledgeFaiMcp`

- ## Quick start (recommended)
    - Create and activate a Python venv (optional but recommended):
        - `python -m venv .venv && .venv\Scripts\activate` (Windows)
        - `python -m venv .venv && source .venv/bin/activate` (Linux/macOS)
    - Install dependencies:
        - CPU (default):
            - 全量安装（包含所有功能）: `pip install -r requirements.txt`
            - 精简安装（仅核心功能）: `pip install -r requirements-minimal.txt`
            - 手动安装核心依赖: `pip install faiss-cpu numpy sentence-transformers fastmcp mcp fastapi uvicorn python-dotenv`
            - 注意: 在Windows上如果`faiss-cpu`安装失败，可以使用conda: `conda install -c conda-forge faiss-cpu numpy`
        - NVIDIA GPU (CUDA):
            - 全量安装（包含所有功能）: `pip install -r requirements-gpu.txt`
            - 精简安装（仅核心功能）: `pip install -r requirements-minimal-gpu.txt`
            - 手动安装核心依赖: 
              - 安装 FAISS GPU: `pip install faiss-gpu`
              - 安装 PyTorch (根据你的 CUDA 版本): 
                - CUDA 12.6: `pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126`
                - CUDA 12.1: `pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121`
                - CUDA 11.8: `pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118`
              - 其他依赖: `pip install sentence-transformers fastmcp mcp fastapi uvicorn python-dotenv`
            - 注意: 需要先安装 NVIDIA 驱动（支持对应 CUDA 版本），确保 PyTorch 能够正确使用 GPU
          
            - **CUDA 验证工具**: 项目包含 `checkCuda.py` 脚本，可用于验证 CUDA 配置是否正确：
                  ```bash
                  python checkCuda.py
                  ```
            该脚本会显示 PyTorch 版本、CUDA 可用性、GPU 设备信息等，帮助诊断 CUDA 相关问题。
        
              ```bash
                PyTorch version: 2.10.0+cu126
                CUDA available: True
                CUDA version: 12.6
                Number of CUDA devices: 1
                Current CUDA device: 0
                CUDA device name: NVIDIA GeForce GTX 1650 Ti
              ```
            
- Environment variables (optional)
    - `FAISS_EMBEDDER_MODEL` — embedding model name (default: `all-MiniLM-L6-v2`)
    - `FAISS_DIM` — embedding dimensionality (default: `384` for `all-MiniLM-L6-v2`)
    - `FAISS_INDEX_PATH` / `FAISS_META_PATH` — paths for index and metadata files (defaults: `faiss.index`, `faiss_meta.json`)
    - `FAISS_DEVICE` — device to use for computation (`cpu` or `cuda`, default: `cpu`)
    - `FAISS_GPU_ID` — GPU ID to use when `FAISS_DEVICE=cuda` (default: `0`)

- Files created
    - `faiss_mcp_server.py` — MCP server implementation (tools: `faiss_add_items`, `faiss_search`, `faiss_save`).
    - `demo_mcp_client.py` — demo client that starts the server via stdio, adds documents, searches, and saves.

- Run server (HTTP SSE transport)
    - `python faiss_mcp_server.py --transport streamable_http --port 8401 --device cpu`
- Run api server
    - `python memory_api.py --port 8425`

- Run demo client (starts server using stdio transport)
    - `python mcp/acknowledgeFaiMcp/demo_mcp_client.py`

- Using the MCP tools (JSON payload examples)
    - Add documents (server computes embeddings):
      ```json
      {"ids":[101,102],"documents":["文本A","文本B"],"metadatas":[{"src":"a"},{"src":"b"}]}
      ```
    - Search by text:
      ```json
      {"query_text":"查找 A","k":5}
      ```
    - Search by embedding:
      ```json
      {"query_embedding":[0.12,0.34,...],"k":5}
      ```

- ## Notes & troubleshooting
    - First run will download sentence-transformers model weights (requires internet). Be patient — model download and CPU/GPU init can take tens of seconds.
    - **国内用户加速模型下载**: 设置环境变量 `HF_ENDPOINT=https://hf-mirror.com` 使用 Hugging Face 镜像源
        - Windows (PowerShell): `$env:HF_ENDPOINT="https://hf-mirror.com"`
        - Linux/macOS: `export HF_ENDPOINT=https://hf-mirror.com`
    - Ensure `FAISS_DIM` matches the embedding model output dimension. Mismatch will raise an error.
    - If you see errors importing `faiss`, try installing via conda-forge as noted above.
    - FAISS removal/true-delete is not implemented for IndexFlat in this lightweight example; to remove items you should rebuild the index from desired items.
    - For NVIDIA GPU support:
        - Ensure you have a compatible NVIDIA GPU with CUDA support
        - Install appropriate NVIDIA drivers and CUDA Toolkit
        - Verify PyTorch can access your GPU with `torch.cuda.is_available()`
        - Set environment variables: `FAISS_DEVICE=cuda` and optionally `FAISS_GPU_ID=N` (where N is your GPU ID)
    
      
- Next steps
    1. Use `demo_mcp_client.py` to validate end-to-end flow.
    2. If you need Docker or a longevity production setup, ask and I'll add Docker/Compose files.

---
Generated by OpenCode — file: `mcp/acknowledgeFaiMcp/README.md`
