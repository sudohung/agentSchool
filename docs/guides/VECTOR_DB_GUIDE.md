# 📚 向量数据库和嵌入模型新手指南

欢迎学习向量数据库和嵌入模型的基础知识！本文档将用简单易懂的方式介绍这些概念及其在 AI 应用中的使用。

## 🎯 什么是向量数据库？

### 简单理解
想象你在图书馆找书：
- **传统数据库**：像按书名或作者查找（精确匹配）
- **向量数据库**：像按内容相似度找书（语义搜索）

### 核心概念
```
文本 → 嵌入模型 → 数字向量 → 向量数据库 → 相似度搜索
```

## 🧠 嵌入模型 explained

### 什么是嵌入（Embedding）？
嵌入就是把文字转换成数字向量的过程：

```
"你好世界" → [0.23, -0.45, 0.67, 0.12, ...] (数百个数字)
"Hello World" → [0.18, -0.39, 0.71, 0.09, ...] (数百个数字)
```

### 常用嵌入模型对比

| 模型名称 | 语言支持 | 特点 | 适用场景 |
|---------|---------|------|----------|
| **paraphrase-multilingual-MiniLM-L12-v2** | 多语言 | 平衡性能 | 通用多语言应用 |
| **all-MiniLM-L6-v2** | 英文为主 | 轻量快速 | 英文应用、资源受限环境 |
| **bge-small-zh-v1.5** | 中文优化 | 中文效果佳 | 中文语义搜索 |

## 🛠️ 实际使用教程

### 1. 环境准备

```bash
# 安装必要依赖
pip install sentence-transformers faiss-cpu numpy
```

### 2. 基础使用示例

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 加载嵌入模型
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 文本转嵌入向量
texts = ["人工智能很有趣", "机器学习很有用", "我喜欢编程"]
embeddings = model.encode(texts)

print(f"向量维度: {len(embeddings[0])}")  # 通常是 384 或 768 维
print(f"向量数量: {len(embeddings)}")
```

### 3. 使用 FAISS 向量数据库

```python
import faiss

# 创建向量索引
dimension = len(embeddings[0])  # 向量维度
index = faiss.IndexFlatL2(dimension)  # L2 距离索引

# 添加向量到数据库
index.add(np.array(embeddings))

# 查询相似向量
query_text = "我对AI技术感兴趣"
query_vector = model.encode([query_text])

# 搜索最相似的 2 个结果
distances, indices = index.search(np.array([query_vector]), k=2)

print("最相似的文本:")
for i, idx in enumerate(indices[0]):
    print(f"{i+1}. {texts[idx]} (距离: {distances[0][i]:.2f})")
```

## 🎮 实际应用场景

### 场景 1：智能问答系统
```python
# 知识库
knowledge_base = [
    "Python是一种编程语言",
    "Java也是一种编程语言", 
    "人工智能是计算机科学的一个分支",
    "机器学习是AI的重要组成部分"
]

# 构建向量数据库
embeddings = model.encode(knowledge_base)
index = faiss.IndexFlatL2(len(embeddings[0]))
index.add(np.array(embeddings))

# 问答功能
def answer_question(question):
    query_vector = model.encode([question])
    distances, indices = index.search(np.array([query_vector]), k=1)
    return knowledge_base[indices[0][0]]

# 测试
print(answer_question("什么是Python？"))  # 应该返回关于Python的回答
```

### 场景 2：文档相似度搜索
```python
# 文档去重示例
documents = [
    "人工智能技术发展迅速",
    "AI技术进步很快",  # 与上面很相似
    "今天天气很好",
    "机器学习算法不断优化"
]

# 找出相似文档
def find_similar_docs(threshold=0.8):
    embeddings = model.encode(documents)
    similar_pairs = []
    
    for i in range(len(documents)):
        for j in range(i+1, len(documents)):
            # 计算余弦相似度
            similarity = np.dot(embeddings[i], embeddings[j]) / \
                        (np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j]))
            if similarity > threshold:
                similar_pairs.append((i, j, similarity))
    
    return similar_pairs

similar_docs = find_similar_docs()
print("相似文档对:", similar_docs)
```

## 🔧 进阶技巧

### 1. 性能优化
```python
# 批量处理提高效率
large_texts = ["文本1", "文本2", ..., "文本1000"]
batch_size = 32

# 分批编码
all_embeddings = []
for i in range(0, len(large_texts), batch_size):
    batch = large_texts[i:i+batch_size]
    batch_embeddings = model.encode(batch)
    all_embeddings.extend(batch_embeddings)
```

### 2. 不同距离度量
```python
# 余弦相似度（更适合文本）
index_cosine = faiss.IndexFlatIP(dimension)  # 内积
faiss.normalize_L2(embeddings)  # 归一化
index_cosine.add(embeddings)

# 欧氏距离（默认）
index_l2 = faiss.IndexFlatL2(dimension)
index_l2.add(embeddings)
```

### 3. 持久化存储
```python
# 保存索引
faiss.write_index(index, "my_vector_index.index")

# 加载索引
loaded_index = faiss.read_index("my_vector_index.index")
```

## 🚨 常见问题解答

### Q: 向量维度越高越好吗？
**A:** 不一定。维度高意味着更精确但计算成本更高。一般 384-768 维就足够大多数应用。

### Q: 如何选择合适的嵌入模型？
**A:** 
- 中文为主 → bge-small-zh-v1.5
- 多语言需求 → paraphrase-multilingual-MiniLM-L12-v2  
- 英文且追求速度 → all-MiniLM-L6-v2

### Q: 向量数据库比传统数据库慢吗？
**A:** 恰恰相反！对于相似度搜索，向量数据库比传统数据库快很多倍。

### Q: 需要多少数据才能看到效果？
**A:** 一般来说，几十到几百条文本就能看到明显的相似度搜索效果。

## 🎯 实践练习

### 练习 1：构建个人笔记搜索系统
```python
# TODO: 实现一个可以搜索个人笔记的系统
# 提示：将笔记内容存入向量数据库，实现语义搜索功能
```

### 练习 2：电影推荐系统
```python
# TODO: 基于电影描述的相似度推荐系统
# 提示：使用电影简介作为文本，找出相似的电影
```

## 📚 进一步学习资源

- [Sentence Transformers 官方文档](https://www.sbert.net/)
- [FAISS 官方教程](https://github.com/facebookresearch/faiss/wiki)
- [向量数据库比较](https://weaviate.io/blog/vector-search-explained)

---

🎉 **恭喜完成基础学习！** 现在你可以开始构建自己的向量搜索应用了！

*有任何问题欢迎在 Issues 中提问*