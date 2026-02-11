# 本地模型路径配置使用说明

## 🎯 本地模型路径配置方法

### 1. 配置文件结构

```json
{
  "device": "nv_gpu",
  "cpu": {
    "backend": "sentence_transformers",
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "model_path": "/path/to/local/model",  // 本地模型路径（可选）
    "dim": 384
  },
  "nv_gpu": {
    "gpu_id": 0,
    "backend": "sentence_transformers",
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "model_path": "C:\\Users\\hung\\Desktop\\workspace\\modelscope\\bge-m3",  // 本地模型路径（优先使用）
    "dim": 1024
  }
}
```

### 2. 配置优先级说明

系统会按照以下优先级加载模型：

1. **最高优先级**：`model_path` - 本地模型路径（如果路径存在）
2. **备选方案**：`model_name` - HuggingFace模型名称（在线下载）

### 3. 本地模型路径配置示例

#### CPU模式配置
```json
{
  "device": "cpu",
  "cpu": {
    "model_path": "/home/user/models/all-MiniLM-L6-v2",
    "dim": 384
  }
}
```

#### NVIDIA GPU模式配置
```json
{
  "device": "nv_gpu",
  "nv_gpu": {
    "gpu_id": 0,
    "model_path": "D:\\models\\bge-large-zh-v1.5",
    "dim": 1024
  }
}
```

#### AMD GPU模式配置（ONNX模型）
```json
{
  "device": "gpu",
  "gpu": {
    "onnx_path": "./models/model.onnx",
    "tokenizer": "BAAI/bge-base-zh-v1.5",
    "dim": 768
  }
}
```

## 📁 本地模型目录结构

### SentenceTransformer模型目录结构
```
your-local-model/
├── config.json
├── modules.json
├── config_sentence_transformers.json
├── 1_Pooling/
│   └── config.json
├── 2_Dense/
│   └── config.json
├── pytorch_model.bin
├── sentence_bert_config.json
└── tokenizer.json
```

### 下载本地模型的方法

#### 方法1：使用transformers-cli下载
```bash
# 安装transformers
pip install transformers

# 下载模型到本地
python -c "
from transformers import AutoModel, AutoTokenizer
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
# 保存到本地
model.save_pretrained('./local_models/all-MiniLM-L6-v2')
tokenizer.save_pretrained('./local_models/all-MiniLM-L6-v2')
"
```

#### 方法2：使用huggingface-hub下载
```bash
pip install huggingface-hub

# 命令行下载
huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 --local-dir ./models/all-MiniLM-L6-v2
```

#### 方法3：手动下载
1. 访问[HuggingFace Models](https://huggingface.co/models)
2. 搜索需要的模型
3. 点击"Files and versions"
4. 下载所有文件到本地目录

## 🔍 验证本地模型配置

### 1. 检查模型路径是否存在
```python
import os
model_path = "C:\\Users\\hung\\Desktop\\workspace\\modelscope\\bge-m3"
print(f"模型路径存在: {os.path.exists(model_path)}")
print(f"路径是目录: {os.path.isdir(model_path)}")
```

### 2. 测试本地模型加载
```python
from sentence_transformers import SentenceTransformer

# 测试本地模型
try:
    model = SentenceTransformer("C:\\Users\\hung\\Desktop\\workspace\\modelscope\\bge-m3")
    print("✅ 本地模型加载成功")
    
    # 测试编码
    embeddings = model.encode(["测试句子"])
    print(f"嵌入维度: {embeddings.shape}")
    
except Exception as e:
    print(f"❌ 本地模型加载失败: {e}")
```

### 3. 验证配置文件
```python
import json

# 读取并验证配置
with open('embedder_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

print("配置验证:")
for device_key in ['cpu', 'nv_gpu', 'gpu']:
    if device_key in config:
        device_config = config[device_key]
        model_path = device_config.get('model_path')
        model_name = device_config.get('model_name')
        
        print(f"\n{device_key.upper()} 配置:")
        if model_path:
            path_exists = os.path.exists(model_path) if model_path else False
            print(f"  本地模型路径: {model_path} ({'存在' if path_exists else '不存在'})")
        print(f"  在线模型名称: {model_name}")
```

## ⚠️ 常见问题及解决方案

### 问题1：路径格式错误
```json
// ❌ 错误的路径格式
"model_path": "C:\Users\model"  // 反斜杠需要转义

// ✅ 正确的路径格式
"model_path": "C:\\Users\\model"  // 双反斜杠
// 或
"model_path": "C:/Users/model"    // 正斜杠
```

### 问题2：模型文件不完整
```bash
# 检查必要文件
required_files = ['config.json', 'pytorch_model.bin', 'tokenizer.json']
model_dir = "your/model/path"

missing_files = [f for f in required_files if not os.path.exists(os.path.join(model_dir, f))]
if missing_files:
    print(f"缺少文件: {missing_files}")
```

### 问题3：权限问题
```bash
# 确保有足够的读取权限
import os
model_path = "/path/to/model"
if os.access(model_path, os.R_OK):
    print("有读取权限")
else:
    print("无读取权限，请检查文件权限")
```

## 🚀 最佳实践建议

### 1. 模型组织结构
```
models/
├── sentence-transformers/
│   ├── all-MiniLM-L6-v2/
│   ├── all-mpnet-base-v2/
│   └── paraphrase-multilingual-MiniLM-L12-v2/
├── bge/
│   ├── bge-small-en-v1.5/
│   └── bge-large-zh-v1.5/
└── indexes/
    ├── cpu/
    ├── gpu/
    └── nv_gpu/
```

### 2. 配置文件模板
```json
{
  "device": "nv_gpu",
  "cpu": {
    "model_path": "./models/sentence-transformers/all-MiniLM-L6-v2",
    "dim": 384
  },
  "nv_gpu": {
    "gpu_id": 0,
    "model_path": "./models/bge/bge-large-zh-v1.5",
    "dim": 1024
  },
  "faiss": {
    "nv_gpu": {
      "index_path": "./indexes/nv_gpu/faiss.index",
      "meta_path": "./indexes/nv_gpu/faiss_meta.json"
    }
  }
}
```

### 3. 环境变量配置
```bash
# 设置环境变量（可选）
export LOCAL_MODEL_PATH="/path/to/models"
export FAISS_INDEX_PATH="./indexes"
```

## 📊 性能对比

| 配置方式 | 加载时间 | 网络依赖 | 适用场景 |
|----------|----------|----------|----------|
| 在线模型 | 较慢 | 需要 | 首次使用、网络良好 |
| 本地模型 | 快速 | 不需要 | 生产环境、离线部署 |
| 混合配置 | 中等 | 备用 | 开发测试、灵活切换 |

现在你可以通过配置`model_path`来使用本地模型了！系统会自动检测路径是否存在，并优先使用本地模型以提高加载速度和可靠性。