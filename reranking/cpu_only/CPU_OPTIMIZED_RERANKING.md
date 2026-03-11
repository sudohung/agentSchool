# 💻 CPU-only环境下的重排优化方案

在个人电脑的CPU-only环境下，我们需要特别考虑计算资源限制，选择轻量级但有效的重排方案。

## 🎯 CPU环境优化原则

### 核心约束条件
- **内存限制**: 通常4-16GB RAM
- **计算能力**: 无GPU加速，依赖CPU多核处理
- **响应时间**: 用户可接受的延迟(<1秒)
- **模型大小**: 避免过大模型导致内存溢出

### 优化目标优先级
1. **推理速度** > 模型精度
2. **内存效率** > 模型复杂度  
3. **实用性** > 理论最优
4. **易部署** > 功能丰富

## 🚀 轻量级重排模型推荐

### 1. CPU友好的嵌入模型

#### A. MiniLM系列 (推荐指数: ⭐⭐⭐⭐⭐)
```python
# 最适合CPU的轻量级模型
models_cpu_friendly = {
    'all-MiniLM-L6-v2': {
        '参数量': 22M,
        '维度': 384,
        '内存占用': ~100MB,
        '特点': '英文优化，速度极快'
    },
    'paraphrase-multilingual-MiniLM-L12-v2': {
        '参数量': 118M,
        '维度': 384, 
        '内存占用': ~400MB,
        '特点': '多语言支持，平衡性能'
    },
    'bge-small-en-v1.5': {
        '参数量': 33M,
        '维度': 384,
        '内存占用': ~150MB,
        '特点': '英文专用，效果优秀'
    }
}
```

#### B. TinyBERT系列
```python
# 超轻量级选项
class CPUEfficientModels:
    def __init__(self):
        # TinyBERT模型，专为CPU优化
        self.tiny_bert_models = {
            'tinybert-4l-312d': {
                '层数': 4,
                '隐藏层': 312,
                '推理速度': '极快',
                '内存': '~50MB'
            },
            'tinybert-6l-768d': {
                '层数': 6, 
                '隐藏层': 768,
                '推理速度': '很快',
                '内存': '~150MB'
            }
        }
```

### 2. 轻量级重排器实现

#### A. 基于规则的快速重排
```python
class RuleBasedReranker:
    """基于规则的轻量级重排器"""
    
    def __init__(self):
        self.weights = {
            'bm25_score': 0.4,
            'popularity': 0.2,
            'recency': 0.2, 
            'length_match': 0.2
        }
    
    def rerank(self, query, candidates):
        """快速规则重排"""
        scored_candidates = []
        
        for candidate in candidates:
            # BM25启发式评分
            bm25_score = self._bm25_score(query, candidate.content)
            
            # 流行度评分
            popularity_score = candidate.features.get('popularity', 0.5)
            
            # 时效性评分
            recency_score = candidate.features.get('recency', 0.5)
            
            # 长度匹配度
            length_score = self._length_matching(query, candidate.content)
            
            # 加权融合
            final_score = (
                self.weights['bm25_score'] * bm25_score +
                self.weights['popularity'] * popularity_score +
                self.weights['recency'] * recency_score +
                self.weights['length_match'] * length_score
            )
            
            scored_candidates.append((final_score, candidate))
        
        # 排序返回
        return sorted(scored_candidates, key=lambda x: x[0], reverse=True)
    
    def _bm25_score(self, query, document):
        """轻量级BM25实现"""
        query_terms = query.lower().split()
        doc_terms = document.lower().split()
        
        k1, b = 1.2, 0.75
        avg_doc_len = 100  # 预估平均文档长度
        doc_len = len(doc_terms)
        
        score = 0
        for term in query_terms:
            tf = doc_terms.count(term)
            if tf > 0:
                # 简化版IDF计算
                idf = np.log(1000 / (tf + 0.5))
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                score += idf * numerator / denominator
        
        return min(1.0, score)  # 归一化到0-1
    
    def _length_matching(self, query, document):
        """长度匹配度计算"""
        query_len = len(query)
        doc_len = len(document)
        ratio = min(query_len, doc_len) / max(query_len, doc_len)
        return ratio
```

#### B. 轻量级机器学习重排
```python
class LightweightMLReranker:
    """轻量级机器学习重排器"""
    
    def __init__(self):
        # 使用轻量级模型
        self.model = None
        self.feature_scaler = StandardScaler()
        self.is_trained = False
    
    def train_lightweight(self, training_data):
        """训练轻量级模型"""
        # 使用线性模型或小规模随机森林
        from sklearn.linear_model import LogisticRegression
        # 或者非常小的随机森林
        from sklearn.ensemble import RandomForestClassifier
        
        self.model = LogisticRegression(max_iter=1000)
        # self.model = RandomForestClassifier(n_estimators=10, max_depth=5)
        
        # 特征工程保持简单
        X, y = self._extract_simple_features(training_data)
        X_scaled = self.feature_scaler.fit_transform(X)
        
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def _extract_simple_features(self, training_data):
        """提取简单特征以减少计算负担"""
        X, y = [], []
        
        for query, docs, labels in training_data:
            for doc, label in zip(docs, labels):
                features = [
                    len(set(query.split()) & set(doc.content.split())),  # 词汇重叠
                    len(doc.content) / (len(query) + 1),  # 长度比例
                    doc.features.get('popularity', 0.5),  # 流行度
                    self._simple_similarity(query, doc.content)  # 简单相似度
                ]
                X.append(features)
                y.append(label)
        
        return np.array(X), np.array(y)
    
    def _simple_similarity(self, text1, text2):
        """简单的文本相似度计算"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0
        return len(words1 & words2) / len(words1 | words2)
```

## ⚡ CPU优化技术

### 1. 批量处理优化
```python
class CPUBatchProcessor:
    """CPU批量处理优化器"""
    
    def __init__(self, batch_size=32):
        self.batch_size = batch_size
        self.thread_pool = ThreadPoolExecutor(max_workers=4)  # 根据CPU核心数调整
    
    def batch_encode(self, texts, model):
        """批量编码优化"""
        results = []
        
        # 分批处理避免内存峰值
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # 并行处理批次
            batch_result = model.encode(batch, show_progress_bar=False)
            results.extend(batch_result)
            
            # 适时释放内存
            if i % (self.batch_size * 4) == 0:
                import gc
                gc.collect()
        
        return np.array(results)
    
    def parallel_rerank(self, queries, candidates_list, reranker):
        """并行重排处理"""
        futures = []
        
        # 提交并行任务
        for query, candidates in zip(queries, candidates_list):
            future = self.thread_pool.submit(reranker.rerank, query, candidates)
            futures.append(future)
        
        # 收集结果
        results = [future.result() for future in futures]
        return results
```

### 2. 内存优化策略
```python
class MemoryEfficientReranker:
    """内存高效重排器"""
    
    def __init__(self):
        self.model_cache = {}
        self.max_cache_size = 1000
    
    def memory_efficient_rerank(self, query, candidates):
        """内存友好的重排实现"""
        # 1. 流式处理避免加载全部数据
        processed_candidates = []
        
        for candidate in candidates:
            # 逐个处理，及时释放中间结果
            score = self._compute_score_efficiently(query, candidate)
            processed_candidates.append((score, candidate))
            
            # 定期清理不需要的对象
            if len(processed_candidates) % 50 == 0:
                self._cleanup_memory()
        
        # 2. 使用就地排序节省内存
        processed_candidates.sort(key=lambda x: x[0], reverse=True)
        return processed_candidates
    
    def _compute_score_efficiently(self, query, candidate):
        """内存高效的分数计算"""
        # 避免创建大的中间数组
        query_words = query.lower().split()
        doc_words = candidate.content.lower().split()
        
        # 使用集合操作而不是循环
        overlap = len(set(query_words) & set(doc_words))
        total_unique = len(set(query_words) | set(doc_words))
        
        return overlap / total_unique if total_unique > 0 else 0
    
    def _cleanup_memory(self):
        """内存清理"""
        import gc
        # 清理缓存中较少使用的项
        if len(self.model_cache) > self.max_cache_size:
            # 移除最老的缓存项
            oldest_key = next(iter(self.model_cache))
            del self.model_cache[oldest_key]
        
        # 强制垃圾回收
        gc.collect()
```

### 3. 模型量化和压缩
```python
class QuantizedReranker:
    """量化重排器"""
    
    def __init__(self):
        self.quantized_model = None
    
    def quantize_model(self, original_model):
        """模型量化以减少内存占用"""
        # 简单的8位量化示例
        def quantize_weights(weights):
            # 将浮点数权重转换为8位整数
            min_val, max_val = weights.min(), weights.max()
            scale = (max_val - min_val) / 255.0
            zero_point = -min_val / scale
            quantized = np.round(weights / scale + zero_point).astype(np.uint8)
            return quantized, scale, zero_point
        
        # 对模型权重进行量化
        quantized_weights = {}
        scales = {}
        zero_points = {}
        
        # 这里简化处理，实际需要遍历模型所有层
        # quantized_weights[layer_name], scales[layer_name], zero_points[layer_name] = \
        #     quantize_weights(original_model.get_layer(layer_name).get_weights())
        
        self.quantized_model = {
            'weights': quantized_weights,
            'scales': scales,
            'zero_points': zero_points
        }
        
        return self.quantized_model
    
    def dequantize_and_predict(self, quantized_input):
        """反量化并预测"""
        # 反量化过程
        # 这是简化的示例，实际实现需要根据具体模型结构调整
        pass
```

## 📊 CPU环境下的性能基准

### 推荐配置组合

#### 入门级配置 (4GB RAM, 双核CPU)
```python
config_entry_level = {
    'model': 'all-MiniLM-L6-v2',  # 最轻量模型
    'batch_size': 16,             # 小批次
    'max_candidates': 100,        # 限制候选数量
    'reranker': 'rule_based',     # 基于规则的重排
    'expected_latency': '<200ms'  # 预期延迟
}
```

#### 标准级配置 (8GB RAM, 四核CPU)
```python
config_standard = {
    'model': 'paraphrase-multilingual-MiniLM-L12-v2',
    'batch_size': 32,
    'max_candidates': 500,
    'reranker': 'lightweight_ml',
    'expected_latency': '<500ms'
}
```

#### 高性能配置 (16GB+ RAM, 八核CPU)
```python
config_high_performance = {
    'model': 'bge-small-en-v1.5',
    'batch_size': 64,
    'max_candidates': 1000,
    'reranker': 'hybrid_approach',  # 混合方法
    'expected_latency': '<800ms'
}
```

### 性能测试代码
```python
class CPUPerformanceBenchmark:
    """CPU性能基准测试"""
    
    def benchmark_configurations(self):
        """测试不同配置的性能"""
        configs = [
            ('入门级', config_entry_level),
            ('标准级', config_standard), 
            ('高性能', config_high_performance)
        ]
        
        results = {}
        
        for config_name, config in configs:
            print(f"测试 {config_name} 配置...")
            
            # 初始化对应配置的重排器
            reranker = self._initialize_reranker(config)
            
            # 运行基准测试
            metrics = self._run_benchmark(reranker, config)
            results[config_name] = metrics
            
            print(f"  处理时间: {metrics['processing_time']:.3f}s")
            print(f"  内存使用: {metrics['memory_usage']:.1f}MB")
            print(f"  准确率: {metrics['accuracy']:.3f}")
            print("-" * 30)
        
        return results
    
    def _initialize_reranker(self, config):
        """根据配置初始化重排器"""
        if config['reranker'] == 'rule_based':
            return RuleBasedReranker()
        elif config['reranker'] == 'lightweight_ml':
            return LightweightMLReranker()
        else:
            return HybridReranker()
    
    def _run_benchmark(self, reranker, config):
        """运行基准测试"""
        import psutil
        import time
        
        # 准备测试数据
        test_data = self._generate_test_data(config['max_candidates'])
        
        # 记录初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 执行重排
        start_time = time.time()
        results = reranker.rerank("测试查询", test_data)
        processing_time = time.time() - start_time
        
        # 记录最终内存
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_usage = final_memory - initial_memory
        
        # 简单的准确率评估
        accuracy = self._evaluate_accuracy(results)
        
        return {
            'processing_time': processing_time,
            'memory_usage': memory_usage,
            'accuracy': accuracy
        }
```

## 🔧 实用优化技巧

### 1. 缓存策略
```python
class SmartCacheReranker:
    """智能缓存重排器"""
    
    def __init__(self, cache_size=1000):
        self.cache = {}
        self.cache_size = cache_size
        self.access_count = {}
    
    def cached_rerank(self, query, candidates):
        """带缓存的重排"""
        # 生成缓存键
        cache_key = self._generate_cache_key(query, candidates)
        
        # 检查缓存
        if cache_key in self.cache:
            self.access_count[cache_key] = self.access_count.get(cache_key, 0) + 1
            return self.cache[cache_key]
        
        # 计算结果
        result = self._compute_rerank(query, candidates)
        
        # 更新缓存
        self._update_cache(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, query, candidates):
        """生成缓存键"""
        # 使用查询和候选文档的哈希值
        candidate_ids = [c.doc_id for c in candidates]
        return hash((query, tuple(sorted(candidate_ids))))
    
    def _update_cache(self, key, value):
        """更新缓存，实现LRU淘汰"""
        if len(self.cache) >= self.cache_size:
            # 移除最少访问的项
            lru_key = min(self.access_count.keys(), key=lambda k: self.access_count[k])
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[key] = value
        self.access_count[key] = 1
```

### 2. 渐进式处理
```python
class ProgressiveReranker:
    """渐进式重排器"""
    
    def __init__(self):
        self.stages = [
            ('fast_filter', 0.3),    # 快速过滤掉30%明显不相关的
            ('medium_rerank', 0.6),  # 中等复杂度重排剩余60%
            ('final_polish', 1.0)    # 精细重排最终100%
        ]
    
    def progressive_rerank(self, query, candidates):
        """渐进式重排处理"""
        current_candidates = candidates
        
        for stage_name, keep_ratio in self.stages:
            # 根据阶段选择不同的重排策略
            if stage_name == 'fast_filter':
                current_candidates = self._fast_filter(query, current_candidates, keep_ratio)
            elif stage_name == 'medium_rerank':
                current_candidates = self._medium_rerank(query, current_candidates, keep_ratio)
            else:  # final_polish
                current_candidates = self._final_rerank(query, current_candidates)
        
        return current_candidates
    
    def _fast_filter(self, query, candidates, keep_ratio):
        """快速过滤阶段"""
        # 使用简单的词频统计快速过滤
        scored = []
        for candidate in candidates:
            score = self._simple_relevance_score(query, candidate.content)
            scored.append((score, candidate))
        
        # 保留top-k
        k = int(len(candidates) * keep_ratio)
        return [candidate for score, candidate in sorted(scored, reverse=True)[:k]]
    
    def _medium_rerank(self, query, candidates, keep_ratio):
        """中等复杂度重排"""
        # 使用轻量级特征工程
        # 实现略...
        pass
    
    def _final_rerank(self, query, candidates):
        """最终精细化重排"""
        # 使用相对复杂的模型进行最终排序
        # 实现略...
        pass
```

## 🎯 最佳实践建议

### 配置选择指南
1. **内存 ≤ 4GB**: 使用入门级配置 + 规则重排
2. **内存 4-8GB**: 使用标准级配置 + 轻量ML重排  
3. **内存 8-16GB**: 使用高性能配置 + 混合重排
4. **内存 > 16GB**: 可以考虑更复杂的模型

### 性能优化要点
- ✅ 优先使用轻量级预训练模型
- ✅ 实施合理的批量处理策略
- ✅ 使用智能缓存减少重复计算
- ✅ 实施渐进式处理避免一次性大量计算
- ✅ 定期进行内存清理和垃圾回收

### 监控和调试
```python
class CPUMonitor:
    """CPU环境监控器"""
    
    def monitor_performance(self, reranker, test_queries):
        """监控重排性能"""
        metrics = {
            'avg_processing_time': [],
            'memory_usage': [],
            'accuracy_scores': []
        }
        
        for query in test_queries:
            # 监控处理时间
            start_time = time.time()
            result = reranker.rerank(query, self.sample_candidates)
            processing_time = time.time() - start_time
            metrics['avg_processing_time'].append(processing_time)
            
            # 监控内存使用
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            metrics['memory_usage'].append(memory_mb)
            
            # 简单的准确率评估
            accuracy = self._simple_accuracy_check(result)
            metrics['accuracy_scores'].append(accuracy)
        
        return self._summarize_metrics(metrics)
```

记住：在CPU-only环境下，实用性往往比理论最优更重要！