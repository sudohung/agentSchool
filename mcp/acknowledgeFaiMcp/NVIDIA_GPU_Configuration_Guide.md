# NVIDIA GPU配置使用说明

## 🎯 正确的配置方法

### 1. 配置文件结构

```yaml
# config.yaml
embedding:
  device: "nv_gpu"  # 或者 "cuda"
  cuda:
    gpu_id: 0           # 指定使用的GPU编号（从0开始）
    model_name: "sentence-transformers/all-MiniLM-L6-v2"  # 嵌入模型名称
  cpu:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"   # CPU模式下的模型
```

### 2. 关键配置项说明

#### device选项：
- `"nv_gpu"` 或 `"cuda"` - 使用NVIDIA GPU加速
- `"gpu"` - 使用AMD GPU（ROCm）
- `"cpu"` - 使用CPU计算（默认）

#### cuda配置节：
- `gpu_id`: 指定要使用的GPU编号
  - `0` - 第一个GPU
  - `1` - 第二个GPU（如果有的话）
  - 依此类推...
- `model_name`: 要加载的SentenceTransformer模型

### 3. 多GPU系统的配置示例

```yaml
# 单GPU系统
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 0
    model_name: "sentence-transformers/all-MiniLM-L6-v2"

# 双GPU系统 - 使用第二块GPU
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 1
    model_name: "sentence-transformers/all-MiniLM-L6-v2"

# 性能更强的模型配置
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 0
    model_name: "sentence-transformers/all-mpnet-base-v2"
```

## 🔍 验证配置是否正确

### 1. 检查GPU可用性
```python
import torch
print("CUDA可用:", torch.cuda.is_available())
print("GPU数量:", torch.cuda.device_count())
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
```

### 2. 测试配置加载
```python
from faiss_mcp_server import _read_embedder_config, get_embedder_for_NVIDIA_gpu

# 读取配置
cfg = _read_embedder_config()
print("当前配置:", cfg)

# 测试GPU初始化
try:
    embedder = get_embedder_for_NVIDIA_gpu(cfg, "nv_gpu")
    print("✅ GPU配置正确，模型加载成功")
except Exception as e:
    print(f"❌ 配置有误: {e}")
```

## ⚠️ 常见配置错误及解决方案

### 错误1：GPU ID超出范围
```yaml
# ❌ 错误配置
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 2  # 系统只有2块GPU(0,1)，但配置了2

# ✅ 正确配置
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 1  # 使用第二块GPU
```

### 错误2：配置层级错误
```yaml
# ❌ 错误配置 - gpu_id放在了错误的位置
embedding:
  device: "nv_gpu"
  gpu_id: 0  # 应该在cuda节内
  cuda:
    model_name: "model"

# ✅ 正确配置
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 0
    model_name: "model"
```

### 错误3：设备类型配置错误
```yaml
# ❌ 错误配置
embedding:
  device: "gpu"  # 这会调用AMD GPU函数
  cuda:
    gpu_id: 0

# ✅ 正确配置
embedding:
  device: "nv_gpu"  # 或 "cuda"
  cuda:
    gpu_id: 0
```

## 🚀 最佳实践建议

### 1. 生产环境推荐配置
```yaml
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 0
    model_name: "sentence-transformers/all-mpnet-base-v2"  # 更高质量的模型
```

### 2. 开发测试配置
```yaml
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 0
    model_name: "sentence-transformers/all-MiniLM-L6-v2"  # 轻量级模型，速度快
```

### 3. 多用户共享GPU配置
```yaml
embedding:
  device: "nv_gpu"
  cuda:
    gpu_id: 0
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
  # 可以为不同用户分配不同的GPU
```

## 📊 性能对比

| 配置 | 推理速度 | 内存占用 | 适用场景 |
|------|----------|----------|----------|
| CPU模式 | 慢 | 低 | 开发测试、小规模数据 |
| GPU模式(gpu_id: 0) | 快 | 中等 | 生产环境、大规模数据 |
| 多GPU并行 | 最快 | 高 | 超大规模数据处理 |

## 🔧 故障排除

如果遇到问题，请按以下步骤检查：

1. **确认CUDA安装**
   ```bash
   nvidia-smi
   ```

2. **确认PyTorch CUDA支持**
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.version.cuda)
   ```

3. **检查配置文件格式**
   ```python
   import yaml
   with open('config.yaml', 'r') as f:
       config = yaml.safe_load(f)
   print(config['embedding'])
   ```

4. **测试模型加载**
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cuda:0")
   ```

这样配置就能正确使用NVIDIA GPU进行嵌入计算了！