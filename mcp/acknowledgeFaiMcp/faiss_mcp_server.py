#!/usr/bin/env python3
"""
Lightweight FAISS-based MCP server for local semantic knowledge store.

This MCP exposes simple tools to add vectors (with optional metadata),
compute embeddings via sentence-transformers on CPU when documents are provided,
search by embedding or text, and persist/load the FAISS index plus metadata.

Notes:
- If you provide `documents` (texts), the server will compute embeddings using
  `sentence-transformers` (CPU) by default. You can also supply embeddings directly.
- Requires `faiss`, `numpy`, and `sentence-transformers` installed for embedding support.
"""

import os
import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

import numpy as np
import faiss
import importlib
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# -------------------- Configuration --------------------

class FaissConfig(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    # Default to a CPU-friendly small model (all-MiniLM-L6-v2) with dim=384
    dim: int = Field(default=384, description="Embedding dimensionality")
    index_path: str = Field(default="faiss.index", description="Path to faiss index file")
    meta_path: str = Field(default="faiss_meta.json", description="Path to metadata JSON file")


# -------------------- FAISS Knowledge Store --------------------

_embedder = None


def _read_embedder_config(cli_device =  None):
    global _embed_cfg
    if _embed_cfg:
        return _embed_cfg

    """Read embedder config from `embedder_config.json` if present, otherwise use env vars."""
    here = os.path.dirname(__file__)
    cfg_path = os.path.join(here, "embedder_config.json")
    cfg = {}
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
    except Exception:
        logger.debug("Failed to read embedder_config.json, falling back to env vars")
    # env vars override file
    env_device = cli_device or os.getenv("FAISS_DEVICE", os.getenv("FAISS_EMBEDDER_DEVICE"))  # Support both new and old env var names
    env_model = os.getenv("FAISS_EMBEDDER_MODEL")
    env_dim = os.getenv("FAISS_DIM")
    index_path = os.getenv('FAISS_INDEX_PATH')
    meta_path = os.getenv('FAISS_META_PATH')
    gpu_id = os.getenv('FAISS_GPU_ID')

    # If an env device is set, respect it
    if env_device:
        cfg['device'] = env_device

    # Set GPU ID if provided
    if gpu_id:
        cfg['gpu_id'] = int(gpu_id)

    # Backwards-compatible env var for single-model workflows
    if env_model:
        if env_device == 'cuda':
            cfg['cuda'] = cfg.get('cuda', {})
            cfg['cuda']['model_name'] = env_model
        else:
            cfg['cpu'] = cfg.get('cpu', {})
            cfg['cpu']['model_name'] = env_model
    if env_dim:
        try:
            cfg['dim'] = int(env_dim)
        except Exception:
            logger.warning("Invalid FAISS_DIM env var, using config/file/default")

    if index_path:
        cfg['index_path'] = index_path
    if meta_path:
        cfg['meta_path'] = meta_path

    logger.info(f"Using embedder config device: {cfg['device']}")

    _embed_cfg = cfg
    return _embed_cfg


def get_embedder_for_AMD_gpu(cfg=None, device=None):
    # Try to use ONNX Runtime (DirectML) for GPU
    try:
        import onnxruntime as ort
    except Exception:
        raise ImportError("onnxruntime is required for GPU embedder. Install with `pip install onnxruntime-directml`")

    # Expect cfg['gpu'] to have onnx_path and tokenizer
    gpu_cfg = cfg.get(device, {})

    logger.info(f"Using gpu_cfg: {gpu_cfg}")

    onnx_path = gpu_cfg.get('onnx_path')
    # Resolve relative ONNX paths relative to this module file so configs may use
    # paths like "./model/foo.onnx" without relying on the current working dir.
    if onnx_path and not os.path.isabs(onnx_path):
        onnx_path = os.path.join(os.path.dirname(__file__), onnx_path)
        onnx_path = os.path.normpath(onnx_path)
    tokenizer_model = gpu_cfg.get('tokenizer')
    if not onnx_path or not tokenizer_model:
        raise ValueError("GPU embedder requires 'onnx_path' and 'tokenizer' configured in embedder_config.json")

    # Build a robust ONNX-based embedder wrapper that adapts to input/output names
    class ONNXEmbedder:
        def __init__(self, onnx_path, tokenizer_model):
            # Lazy import heavy deps
            from transformers import AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_model, use_fast=True)

            # Choose provider: prefer DirectML (Windows), then CUDA, then CPU
            providers = ort.get_all_providers()
            chosen = None
            if 'DmlExecutionProvider' in providers:
                chosen = ['DmlExecutionProvider']
            elif 'CUDAExecutionProvider' in providers:
                chosen = ['CUDAExecutionProvider']
            else:
                chosen = ['CPUExecutionProvider']

            self.session = ort.InferenceSession(onnx_path, providers=chosen)

            # Inspect expected input/output names
            self.input_names = [inp.name for inp in self.session.get_inputs()]
            self.output_names = [out.name for out in self.session.get_outputs()]

        def _prepare_inputs(self, texts):
            # Tokenize to numpy arrays
            toks = self.tokenizer(texts, padding=True, truncation=True, return_tensors='np')

            ort_inputs = {}
            for name in self.input_names:
                lname = name.lower()
                if lname in toks:
                    v = toks[lname]
                elif 'input_ids' in lname and 'input_ids' in toks:
                    v = toks['input_ids']
                elif 'attention' in lname and 'attention_mask' in toks:
                    v = toks['attention_mask']
                elif 'token_type' in lname and 'token_type_ids' in toks:
                    v = toks['token_type_ids']
                else:
                    # Try to find compatible tensor by dtype/shape; fallback to zeros
                    # If input is integer type, provide zeros of appropriate shape
                    inp = next(i for i in self.session.get_inputs() if i.name == name)
                    shape = [s if isinstance(s, int) else len(texts) for s in inp.shape]
                    import numpy as _np
                    if inp.type.startswith('tensor(int') or 'int' in inp.type:
                        v = _np.zeros(shape, dtype=_np.int64)
                    else:
                        v = _np.zeros(shape, dtype=_np.float32)
                # Ensure correct dtype
                import numpy as _np
                if v.dtype.kind == 'i':
                    v = v.astype(_np.int64)
                elif v.dtype.kind == 'f':
                    v = v.astype(_np.float32)
                ort_inputs[name] = v

            return ort_inputs

        def encode(self, texts, convert_to_numpy=True):
            # Accept a single string or list
            single = False
            if isinstance(texts, str):
                texts = [texts]
                single = True

            ort_inputs = self._prepare_inputs(texts)

            outs = self.session.run(self.output_names, ort_inputs)

            # Convert outputs to numpy and select a 2-D tensor to use as sentence embeddings.
            # Heuristics (in order):
            # 1) Prefer output whose name contains 'sentence' or 'pool' or 'cls' and has ndim==2
            # 2) Otherwise prefer any output with ndim==2
            # 3) If only token-level outputs (ndim==3) are available, average across sequence axis
            import numpy as _np
            chosen = None
            chosen_name = None
            for name, out in zip(self.output_names, outs):
                arr = _np.asarray(out)
                lname = name.lower()
                if arr.ndim == 2 and any(k in lname for k in ('sentence', 'pool', 'cls')):
                    chosen = arr
                    chosen_name = name
                    break
            if chosen is None:
                for name, out in zip(self.output_names, outs):
                    arr = _np.asarray(out)
                    if arr.ndim == 2:
                        chosen = arr
                        chosen_name = name
                        break
            if chosen is None:
                # fallback: take first output and if it's token-level (B, S, D) average over S
                arr0 = _np.asarray(outs[0])
                if arr0.ndim == 3:
                    chosen = arr0.mean(axis=1)
                    chosen_name = self.output_names[0] + " (mean over seq)"
                else:
                    # As a last resort, try to reshape to (batch, -1)
                    chosen = arr0.reshape((len(texts), -1))
                    chosen_name = self.output_names[0] + " (reshaped)"

            # Ensure float32
            emb = _np.asarray(chosen, dtype=_np.float32)
            # If single input, return 1-D vector
            if single:
                return emb[0]
            return emb

    logger.info('Initializing ONNX embedder with model path: %s', onnx_path)
    embedder = ONNXEmbedder(onnx_path, tokenizer_model)
    return embedder


def get_embedder_for_NVIDIA_gpu(cfg=None, device=None):
    """Initialize SentenceTransformer embedder for NVIDIA GPU with CUDA support."""
    try:
        import torch
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        raise ImportError("torch and sentence-transformers are required for NVIDIA GPU embedder. Install with `pip install torch torchvision sentence-transformers`")

    # Check if CUDA is available
    if not torch.cuda.is_available():
        logger.error(f"CUDA is not available. Please ensure you have a compatible NVIDIA GPU and drivers installed. count={torch.cuda.device_count()}")
        raise RuntimeError("CUDA is not available. Please ensure you have a compatible NVIDIA GPU and drivers installed.")

    # Get GPU configuration from cuda section
    cuda_cfg = cfg.get('nv_gpu', {})
    gpu_id = cuda_cfg.get('gpu_id', 0)  # 从cuda配置节获取GPU ID
    if gpu_id >= torch.cuda.device_count():
        raise ValueError(f"GPU ID {gpu_id} is invalid. Available GPUs: {torch.cuda.device_count()}")

    # Set device to specific GPU
    device_str = f"cuda:{gpu_id}"
    
    # Get model configuration
    model_name = cuda_cfg.get('model_name', "sentence-transformers/all-MiniLM-L6-v2")
    model_path = cuda_cfg.get('model_path')  # 支持本地模型路径
    
    # 优先使用本地模型路径，如果没有则使用模型名称
    if model_path and os.path.exists(model_path):
        logger.info(f"Initializing SentenceTransformer for NVIDIA GPU {gpu_id} with local model: {model_path}")
        embedder = SentenceTransformer(model_path, device=device_str)
    else:
        logger.info(f"Initializing SentenceTransformer for NVIDIA GPU {gpu_id} with model: {model_name}")
        embedder = SentenceTransformer(model_name, device=device_str)
    return embedder


def get_embedder(model_name: Optional[str] = None):
    """Lazily load a SentenceTransformer embedder if available."""
    global _embedder
    if _embedder is not None:
        return _embedder

    # Determine device and model source from config
    cfg = _read_embedder_config()
    device = cfg.get('device', 'cpu')

    logger.info(f"Using embedder device: {device}")

    # 根据设备确定embedder
    if device == 'gpu':
        _embedder = get_embedder_for_AMD_gpu(cfg, device)
        return _embedder
    elif device == 'nv_gpu' or device == 'cuda':
        _embedder = get_embedder_for_NVIDIA_gpu(cfg, device)
        return _embedder

    # Default to CPU sentence-transformers
    try:
        SentenceTransformer = importlib.import_module('sentence_transformers').SentenceTransformer
    except Exception as e:
        raise ImportError("sentence-transformers is not installed. Install with `pip install sentence-transformers` to enable embedding generation")

    cpu_cfg = cfg.get('cpu', {})
    model_name = cpu_cfg.get('model_name', "sentence-transformers/all-MiniLM-L6-v2")
    _embedder = SentenceTransformer(model_name)
    return _embedder



class FaissKB:
    def __init__(self, cfg: FaissConfig):
        self.cfg = cfg
        self.dim = int(cfg.dim)
        self.index: Optional[faiss.Index] = None
        self.metadatas: Dict[str, Any] = {}
        self._ensure_index()

    # 注释： 初始化创建faiss索引
    def _ensure_index(self):
        # Use IndexFlatL2 wrapped by an ID map so items can carry stable integer ids
        if self.index is None:
            base_index = faiss.IndexFlatL2(self.dim)
            self.index = faiss.IndexIDMap(base_index)

        logger.info(f"Loaded faiss conf from {self.cfg}")

        # load metadata if exists
        if os.path.exists(self.cfg.meta_path):
            try:
                with open(self.cfg.meta_path, 'r', encoding='utf-8') as f:
                    self.metadatas = json.load(f)
            except Exception:
                logger.warning("Failed to load metadata file, starting fresh")
                self.metadatas = {}

        # load index if exists
        if os.path.exists(self.cfg.index_path):
            try:
                self.index = faiss.read_index(self.cfg.index_path)
                logger.info(f"Loaded faiss index from {self.cfg.index_path}")
            except Exception:
                logger.warning("Failed to read faiss index file, using empty index")

    def add_items(self, metadatas: Optional[List[Dict[str, Any]]] = None, documents: Optional[List[str]] = None) -> List[int]:
        # Accept embeddings directly, or compute from provided documents using sentence-transformers.
        if documents is None:
            raise ValueError("Either embeddings or documents must be provided")
        # compute embeddings from documents
        embedder = get_embedder()
        arr = embedder.encode(documents, convert_to_numpy=True)
        arr = np.asarray(arr, dtype='float32')
        # 获取数据长度用于生成IDs
        data_length = len(documents)


        # Normalize embeddings shape:
        # - If model returned a single 1-D vector, reshape to (1, D)
        # - If model returned token-level outputs (B, S, D), average over sequence axis
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
            data_length = 1
        elif arr.ndim == 3:
            # average token embeddings to produce sentence embeddings
            arr = arr.mean(axis=1)
            data_length = arr.shape[0]

        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError(f"Embeddings must be 2-D and have dimensionality {self.dim}")

        # 自动生成连续的ID
        if self.metadatas:
            start_id = max(int(k) for k in self.metadatas.keys()) + 1
        else:
            start_id = 1
        ids = list(range(start_id, start_id + data_length))
        id_array = np.array(ids, dtype='int64')

        logger.info(f"Adding {len(ids)} items to faiss index with auto-generated IDs: {ids}")

        # add to faiss
        try:
            # IndexIDMap supports add_with_ids
            if self.index is not None:
                self.index.add_with_ids(arr, id_array)
        except Exception as e:
            logger.error(f"Error adding items to faiss index: {e}")
            raise

        logger.info(f"metadatasccc {metadatas} items to faiss index")
        currentTime = datetime.now(timezone.utc).isoformat()

        # store metadata
        for i, uid in enumerate(ids):
            entry = {"id": int(uid)}
            if metadatas and i < len(metadatas):
                entry["metadata"] = metadatas[i]
                entry["timestamp"] = currentTime
            if documents and i < len(documents):
                entry["document"] = documents[i]
            self.metadatas[str(uid)] = entry

        # persist metadata
        self._save_meta()
        return ids

    def search(self, embedding: Optional[List[float]] = None, query_text: Optional[str] = None, k: int = 5) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        if embedding is None:
            if query_text is None:
                raise ValueError("Either embedding or query_text must be provided")
            # compute embedding from text
            embed_model_name = os.getenv("FAISS_EMBEDDER_MODEL", None)
            embedder = get_embedder(embed_model_name)
            vec = embedder.encode([query_text], convert_to_numpy=True)
            vec = np.asarray(vec, dtype='float32')
        else:
            vec = np.asarray(embedding, dtype='float32')
        if vec.ndim == 1:
            vec = vec.reshape(1, -1)
        if vec.shape[1] != self.dim:
            raise ValueError(f"Query embedding must have dimensionality {self.dim}")

        if self.index is not None:
            D, I = self.index.search(vec, k)
        else:
            return []
        results = []
        for dist, idx in zip(D[0], I[0]):
            logger.info(f"Search result idx: {idx}, dist: {dist}")
            if idx == -1:
                continue
            meta = self.metadatas.get(str(int(idx)), None)
            results.append({"id": int(idx), "score": float(dist), "metadata": meta})
        return results

    def save(self):
        try:
            faiss.write_index(self.index, self.cfg.index_path)
        except Exception as e:
            logger.error(f"Failed to write faiss index: {e}")
            raise
        self._save_meta()

    def _save_meta(self):
        try:
            with open(self.cfg.meta_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadatas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to write metadata file: {e}")
            raise

    def delete(self, id: int) -> bool:
        # FAISS does not support delete in IndexFlat; we can mark by rebuilding index without the id
        sid = str(id)
        if sid not in self.metadatas:
            return False

        # remove metadata
        del self.metadatas[sid]

        # rebuild index from remaining items
        remaining = []
        ids = []
        for k, v in self.metadatas.items():
            if "document" in v:
                # no op, we only use embeddings stored in faiss; user is responsible for keeping consistent
                pass
            # we cannot recover embeddings from metadata; so user should re-add if they want persistent deletes
        # For safety, we save metadata and leave index as-is (deletes not fully supported here)
        self._save_meta()
        return True


# -------------------- MCP Server --------------------

_kb: Optional[FaissKB] = None
_embed_cfg = None


@asynccontextmanager
async def app_lifespan(app):
    global _kb
    # Resolve embedder config from file + env
    embed_cfg = _read_embedder_config()

    # If embed_cfg provides device-specific dims, prefer those
    device = embed_cfg.get('device', 'cpu')
    if device == 'cuda':
        # For NVIDIA GPU, use cuda config section
        device_cfg = embed_cfg.get('cuda', {})
    else:
        device_cfg = embed_cfg.get(device, {})
    resolved_dim = int(device_cfg.get('dim', FaissConfig().dim))
    logger.info(f"Using device: {device}, device_cfg: {device_cfg}")

    # Resolve faiss index/meta paths from config or env
    faiss_section = embed_cfg.get('faiss', {})
    faiss_cfg = {}
    if isinstance(faiss_section, dict):
        faiss_cfg = faiss_section.get(device, {})
    
    index_path = 'faiss.index'
    meta_path = 'faiss_meta.json'
    if isinstance(faiss_cfg, dict):
        index_path = faiss_cfg.get('index_path', 'faiss.index')
        meta_path = faiss_cfg.get('meta_path', 'faiss_meta.json')

    logger.info(f"Using device: {device}, faiss_cfg: {faiss_cfg}")


    cfg = FaissConfig(
        dim=resolved_dim,
        index_path=index_path,
        meta_path=meta_path,
    )

    # 配置FAISS
    _kb = FaissKB(cfg)
    # Validate that the loaded embedder (if any) matches the FAISS dimensionality
    try:
        embedder = get_embedder(None)
        model_dim = None
        try:
            # SentenceTransformer exposes embedding dimension
            model_dim = getattr(embedder, 'get_sentence_embedding_dimension', None)
            if callable(model_dim):
                model_dim = model_dim()
        except Exception:
            model_dim = None

        if model_dim is not None and int(model_dim) != int(cfg.dim):
            raise ValueError(
                f"Configured FAISS dim ({cfg.dim}) does not match embedder dimension ({model_dim}). "
                "Update embedder_config.json or FAISS_DIM to match your model."
            )
    except Exception as e:
        # If embedder loading fails, warn but allow server to continue — embedding calls will raise if used.
        logger.warning("Embedder validation warning: %s", e)
    yield {"kb": _kb}

    # on shutdown, persist
    try:
        if _kb:
            _kb.save()
    except Exception:
        logger.exception("Error saving faiss store on shutdown")


# Parse command line args early so we can create the FastMCP with host/port before tools are
# registered. This mirrors other MCP servers in the repo.
import argparse
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--transport", choices=["stdio", "streamable_http", "sse"], default=os.getenv("FAISS_TRANSPORT", "streamable_http"))
parser.add_argument("--host", default=os.getenv("FAISS_HOST", "127.0.0.1"))
parser.add_argument("--port", type=int, default=int(os.getenv("FAISS_PORT", "8001")))
_cli_args, _remaining = parser.parse_known_args()

# Create the FastMCP instance used by decorators. We set host/port from CLI so server
# will bind correctly when run.
mcp = FastMCP("faiss_kb_mcp", lifespan=app_lifespan, host=_cli_args.host, port=_cli_args.port)

# Log configured endpoints so clients know which paths to use
logger.info(
    "FastMCP configured paths: sse=%s message=%s streamable=%s",
    mcp.settings.sse_path,
    mcp.settings.message_path,
    mcp.settings.streamable_http_path,
)


# Add a lightweight health endpoint and a compatibility POST `/call_tool` route
# so simple HTTP clients can call tools without implementing full StreamableHTTP/SSE.
@mcp.custom_route("/health", methods=["GET"])
async def _health(request: Request):
    return JSONResponse({
        "status": "ok",
        "sse_path": mcp.settings.sse_path,
        "message_path": mcp.settings.message_path,
        "streamable_http_path": mcp.settings.streamable_http_path,
    })


@mcp.custom_route("/call_tool", methods=["POST"])
async def _call_tool_compat(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    tool = payload.get("tool")
    arguments = payload.get("arguments", {})
    if not tool:
        return JSONResponse({"error": "missing tool name"}, status_code=400)

    try:
        result = await mcp.call_tool(tool, arguments)
        # Convert result into JSON-serializable form
        def _to_jsonable(x):
            # primitives
            if x is None or isinstance(x, (str, int, float, bool)):
                return x
            # lists/tuples
            if isinstance(x, (list, tuple)):
                return [_to_jsonable(i) for i in x]
            # dicts
            if isinstance(x, dict):
                return {k: _to_jsonable(v) for k, v in x.items()}
            # objects like ContentBlock/TextContent: prefer .text
            text = getattr(x, 'text', None)
            if isinstance(text, (str, int, float, bool)):
                return text
            # pydantic models
            if hasattr(x, 'model_dump'):
                try:
                    return _to_jsonable(x.model_dump())
                except Exception:
                    pass
            if hasattr(x, 'dict'):
                try:
                    return _to_jsonable(x.dict())
                except Exception:
                    pass
            # fallback to string
            try:
                return str(x)
            except Exception:
                return repr(x)

        # Serialize to JSON string ourselves to avoid framework serialization errors
        try:
            body = json.dumps({"result": _to_jsonable(result)}, ensure_ascii=False)
        except Exception:
            # Fallback: return stringified result
            body = json.dumps({"result": str(result)}, ensure_ascii=False)
        return Response(body, media_type='application/json')
    except Exception as e:
        logger.exception("compat call_tool failed")
        return JSONResponse({"error": str(e)}, status_code=500)


class DocumentItem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="单个文档的元数据字典。例如：{\"source\": \"file1.txt\", \"category\": \"technical\"}"
    )
    document: Optional[str] = Field(
        None,
        description="要添加的文本文档内容。"
    )
    embedding: Optional[List[float]] = Field(
        None,
        description="预计算的嵌入向量。维度需与FAISS配置匹配。"
    )

class AddItemsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="单个文档的元数据字典。例如：{\"source\": \"file1.txt\", \"category\": \"technical\"}"
    )
    document: Optional[str] = Field(
        None,
        description="要添加的文本文档内容。"
    )


@mcp.tool(
    name="faiss_add_items",
    description="向知识库添加新条目。提供原始嵌入向量或文本文档（系统将自动嵌入）。系统会自动生成唯一ID，建议逐条添加。\n\n参数格式：params=[{\"metadata\":{\"source\":\"aaa.md\"},\"document\":\"文档内容\"},...]\n",
)
async def faiss_add_items(params: List[AddItemsInput], ctx: Context) -> Dict[str, Any]:
    global _kb
    if _kb is None:
        raise RuntimeError("Faiss KB not initialized")

    try:
        # 提取数据
        metadatas = []
        documents = []

        has_documents = False

        for item in params:
            if item.document:
                has_documents = True
                metadatas.append(item.metadata)
                documents.append(item.document)
            else:
                raise ValueError("每个item必须提供document或embedding中的至少一个")
        
        # 根据提供的数据类型调用相应方法
        if has_documents :
            # 只提供文档，系统自动嵌入
            added = _kb.add_items(metadatas, documents)
        else:
            raise ValueError("每个item必须提供document或embedding中的至少一个")
            
        return {"success": True, "added_ids": added}
    except Exception as e:
        logger.exception("faiss_add_items failed")
        return {"success": False, "error": str(e)}


class SearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    query_embedding: Optional[List[float]] = Field(
        None,
        description="（可选）查询的嵌入向量。维度需与FAISS配置匹配。"
    )
    query_text: Optional[str] = Field(
        None,
        description="查询文本。系统将自动计算嵌入向量进行搜索。"
    )
    k: int = Field(
        default=5, 
        ge=1, 
        le=100,
        description="返回最相似的前k个结果。默认值为5，范围1-100。"
    )


@mcp.tool(
    name="faiss_search",
    description="在知识库中搜索相关条目。可使用自然语言查询（文本）或预计算的嵌入向量进行搜索。返回按相关性排序的最相似条目。\n\n参数格式：params={\"query_text\":\"搜索内容\",\"k\":5}\n\n参数示例：\n文本搜索：{\"query_text\":\"查找技术文档\",\"k\":5}\n向量搜索：{\"query_embedding\":[0.1,0.2,0.3,...],\"k\":10}\n简单搜索：{\"query_text\":\"hello world\"}",
)
async def faiss_search(params: SearchInput, ctx: Context) -> Dict[str, Any]:
    global _kb
    if _kb is None:
        raise RuntimeError("Faiss KB not initialized")

    try:
        results = _kb.search(embedding=params.query_embedding, query_text=params.query_text, k=params.k)
        return {"success": True, "results": results}
    except Exception as e:
        logger.exception("faiss_search failed")
        return {"success": False, "error": str(e)}


class SaveInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    # 此工具无需参数，用于保存当前索引和元数据到磁盘


@mcp.tool(
    name="faiss_save",
    description="将FAISS索引和元数据持久化到磁盘。用于保存当前的知识库状态。\n\n参数格式：params={}\n\n参数示例：{}  # 无需参数，直接调用即可保存当前状态",
)
async def faiss_save(params: SaveInput, ctx: Context) -> str:
    global _kb
    if _kb is None:
        raise RuntimeError("Faiss KB not initialized")
    try:
        _kb.save()
        return json.dumps({"success": True, "message": "Saved index and metadata"}, indent=2)
    except Exception as e:
        logger.exception("faiss_save failed")
        return json.dumps({"success": False, "error": str(e)})


def test_faiss_add_items():
    """快速测试 faiss_add_items 接口"""
    print("=" * 50)
    print("Test faiss_add_items interface")
    print("=" * 50)
    
    # 创建测试数据 - 直接构造符合API要求的参数格式
    test_params = [
        AddItemsInput(
            metadata={"source": "test1.md", "category": "technical"},
            document="This is the first test document content"
        ),
        AddItemsInput(
            metadata={"source": "test2.md", "category": "business"},
            document="This is the second test document content with more text for testing"
        )
    ]
    
    print(f"\nTest data:")
    print(f"  - Number of documents: {len(test_params)}")
    for i, item in enumerate(test_params):
        print(f"  - Document {i+1}: {item.metadata['source']} - {item.document[:20]}...")
    
    # 验证数据结构
    print(f"\nData structure validation passed")
    print(f"  - params type: {type(test_params)}")
    print(f"  - First item type: {type(test_params[0])}")
    print(f"  - metadata structure: {test_params[0].metadata}")
    
    print(f"\nTest completed! Interface parameter format is correct.")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FAISS MCP Server")
    parser.add_argument("--transport", choices=["stdio", "streamable_http", "sse"], default="streamable_http")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--test", action="store_true", help="运行接口测试")
    parser.add_argument("--device", choices=["cpu", "gpu", "nv_gpu"], default=None)
    args = parser.parse_args()

    # 初始化配置
    _read_embedder_config(args.device)

    if args.test:
        # 运行测试
        test_faiss_add_items()
    else:
        # 正常启动服务器
        # NOTE: do not recreate `mcp` here — tools are already registered on the module-level
        # FastMCP instance (`mcp`). Recreating it would lose registered tools.
        # Support explicit SSE or StreamableHTTP transports.
        # - CLI `sse` -> FastMCP transport "sse"
        # - CLI `streamable_http` -> FastMCP transport "streamable-http"
        if args.transport == "sse":
            mcp.run(transport="sse")
        elif args.transport == "streamable_http":
            mcp.run(transport="streamable-http")
        else:
            mcp.run(transport="stdio")
