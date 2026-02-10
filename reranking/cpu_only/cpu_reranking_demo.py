"""
CPU-only环境下的重排优化实战演示
CPU-Optimized Reranking Demo for Personal Computers
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import time
import psutil
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import gc

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Document:
    """文档数据结构"""
    doc_id: int
    content: str
    features: Dict[str, float] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = {}

@dataclass
class RerankResult:
    """重排结果"""
    doc_id: int
    content: str
    score: float
    rank: int

class CPUEfficientModels:
    """CPU友好的模型管理器"""
    
    def __init__(self):
        self.models = {}
        self.current_model = None
        self.model_configs = {
            'mini': {
                'name': 'all-MiniLM-L6-v2',
                'dim': 384,
                'memory_mb': 100,
                'speed_rating': 5  # 1-5评分
            },
            'multilingual': {
                'name': 'paraphrase-multilingual-MiniLM-L12-v2', 
                'dim': 384,
                'memory_mb': 400,
                'speed_rating': 3
            },
            'bge_small': {
                'name': 'bge-small-en-v1.5',
                'dim': 384,
                'memory_mb': 150,
                'speed_rating': 4
            }
        }
    
    def load_model(self, model_type: str = 'mini'):
        """加载CPU友好的模型"""
        if model_type not in self.model_configs:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        config = self.model_configs[model_type]
        logger.info(f"📥 加载模型: {config['name']} (内存占用约{config['memory_mb']}MB)")
        
        try:
            # 检查内存是否充足
            available_memory = self._get_available_memory()
            if available_memory < config['memory_mb'] * 2:  # 预留一些内存
                logger.warning(f"⚠️ 内存可能不足，当前可用: {available_memory}MB")
            
            self.current_model = SentenceTransformer(config['name'])
            self.models[model_type] = self.current_model
            logger.info(f"✅ 模型加载成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            return False
    
    def _get_available_memory(self) -> int:
        """获取可用内存(MB)"""
        process = psutil.Process()
        memory_info = process.memory_info()
        available = psutil.virtual_memory().available / (1024 * 1024)
        return int(available)

class RuleBasedReranker:
    """基于规则的轻量级重排器"""
    
    def __init__(self):
        self.weights = {
            'bm25': 0.4,
            'popularity': 0.2,
            'recency': 0.2,
            'length_match': 0.2
        }
        logger.info("✅ 规则重排器初始化完成")
    
    def rerank(self, query: str, candidates: List[Document], top_k: int = 10) -> List[RerankResult]:
        """基于规则的重排"""
        start_time = time.time()
        
        scored_candidates = []
        for doc in candidates:
            # 计算各项分数
            bm25_score = self._calculate_bm25(query, doc.content)
            popularity_score = doc.features.get('popularity', 0.5)
            recency_score = doc.features.get('recency', 0.5)
            length_score = self._calculate_length_match(query, doc.content)
            
            # 加权融合
            final_score = (
                self.weights['bm25'] * bm25_score +
                self.weights['popularity'] * popularity_score +
                self.weights['recency'] * recency_score +
                self.weights['length_match'] * length_score
            )
            
            scored_candidates.append((final_score, doc))
        
        # 排序并截取top-k
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored_candidates[:top_k]
        
        # 构建结果
        results = []
        for rank, (score, doc) in enumerate(top_candidates, 1):
            results.append(RerankResult(
                doc_id=doc.doc_id,
                content=doc.content,
                score=float(score),
                rank=rank
            ))
        
        processing_time = time.time() - start_time
        logger.info(f"🔄 规则重排完成: {len(candidates)}→{len(results)} 项，耗时{processing_time:.4f}秒")
        
        return results
    
    def _calculate_bm25(self, query: str, document: str) -> float:
        """轻量级BM25计算"""
        query_terms = query.lower().split()
        doc_terms = document.lower().split()
        
        if not query_terms or not doc_terms:
            return 0.0
        
        k1, b = 1.2, 0.75
        avg_doc_len = 100  # 预估平均文档长度
        doc_len = len(doc_terms)
        
        score = 0.0
        for term in set(query_terms):  # 去重避免重复计算
            tf = doc_terms.count(term)
            if tf > 0:
                # 简化版IDF
                idf = np.log(1000 / (tf + 0.5))
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                score += idf * numerator / denominator
        
        # 归一化到0-1范围
        return min(1.0, score / len(query_terms))
    
    def _calculate_length_match(self, query: str, document: str) -> float:
        """长度匹配度计算"""
        query_len = len(query)
        doc_len = len(document)
        if query_len == 0 or doc_len == 0:
            return 0.0
        ratio = min(query_len, doc_len) / max(query_len, doc_len)
        return ratio

class LightweightMLReranker:
    """轻量级机器学习重排器"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = ['word_overlap', 'length_ratio', 'popularity', 'simple_sim']
        self.is_trained = False
        logger.info("✅ 轻量级ML重排器初始化完成")
    
    def train(self, training_data: List[Tuple[str, List[Document], List[int]]]):
        """训练轻量级ML模型"""
        logger.info("🏋️ 开始训练轻量级ML模型...")
        
        X, y = [], []
        
        for query, docs, relevance_labels in training_data:
            for doc, label in zip(docs, relevance_labels):
                # 提取简单特征
                features = self._extract_features(query, doc)
                X.append(features)
                # 简单的二分类标签
                y.append(1 if label > 0 else 0)
        
        if len(X) > 10:  # 需要足够的训练样本
            X_scaled = self.scaler.fit_transform(X)
            # 使用逻辑回归（轻量级）
            self.model = LogisticRegression(max_iter=1000, C=1.0)
            self.model.fit(X_scaled, y)
            self.is_trained = True
            logger.info(f"✅ ML模型训练完成，使用了{len(X)}个样本")
        else:
            logger.warning("⚠️ 训练样本不足，无法训练ML模型")
    
    def rerank(self, query: str, candidates: List[Document], top_k: int = 10) -> List[RerankResult]:
        """ML重排"""
        if not self.is_trained or not self.model:
            logger.warning("⚠️ ML模型未训练，使用默认排序")
            return self._default_rerank(candidates, top_k)
        
        start_time = time.time()
        
        # 提取特征
        features_list = []
        for doc in candidates:
            features = self._extract_features(query, doc)
            features_list.append(features)
        
        # 预测概率
        features_scaled = self.scaler.transform(features_list)
        probabilities = self.model.predict_proba(features_scaled)[:, 1]  # 正类概率
        
        # 构建结果
        scored_candidates = list(zip(probabilities, candidates))
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for rank, (score, doc) in enumerate(scored_candidates[:top_k], 1):
            results.append(RerankResult(
                doc_id=doc.doc_id,
                content=doc.content,
                score=float(score),
                rank=rank
            ))
        
        processing_time = time.time() - start_time
        logger.info(f"🔄 ML重排完成: {len(candidates)}→{len(results)} 项，耗时{processing_time:.4f}秒")
        
        return results
    
    def _extract_features(self, query: str, doc: Document) -> List[float]:
        """提取简单特征"""
        query_words = set(query.lower().split())
        doc_words = set(doc.content.lower().split())
        
        # 词汇重叠
        word_overlap = len(query_words & doc_words)
        
        # 长度比例
        length_ratio = len(doc.content) / (len(query) + 1)
        
        # 流行度
        popularity = doc.features.get('popularity', 0.5)
        
        # 简单相似度
        simple_sim = len(query_words & doc_words) / len(query_words | doc_words) if (query_words | doc_words) else 0
        
        return [word_overlap, length_ratio, popularity, simple_sim]
    
    def _default_rerank(self, candidates: List[Document], top_k: int) -> List[RerankResult]:
        """默认排序（按文档ID）"""
        results = []
        for rank, doc in enumerate(candidates[:top_k], 1):
            results.append(RerankResult(
                doc_id=doc.doc_id,
                content=doc.content,
                score=1.0/rank,  # 简单位次分数
                rank=rank
            ))
        return results

class BatchProcessor:
    """批量处理器 - CPU优化"""
    
    def __init__(self, batch_size: int = 32, max_workers: int = 4):
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"✅ 批量处理器初始化完成 (batch_size={batch_size}, workers={max_workers})")
    
    def batch_process(self, items: List, process_func, *args, **kwargs):
        """批量处理"""
        results = []
        
        # 分批处理
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # 批内并行处理
            batch_results = list(self.executor.map(
                lambda item: process_func(item, *args, **kwargs), batch
            ))
            
            results.extend(batch_results)
            
            # 定期内存清理
            if i % (self.batch_size * 4) == 0:
                self._cleanup_memory()
        
        return results
    
    def _cleanup_memory(self):
        """内存清理"""
        gc.collect()

class CPURerankingPipeline:
    """CPU优化的重排流水线"""
    
    def __init__(self, system_memory_mb: int = None):
        self.system_memory = system_memory_mb or self._detect_system_memory()
        self.models = CPUEfficientModels()
        self.batch_processor = BatchProcessor()
        self.rule_reranker = RuleBasedReranker()
        self.ml_reranker = LightweightMLReranker()
        
        # 根据内存自动选择配置
        self.config = self._select_optimal_config()
        logger.info(f"✅ CPU重排流水线初始化完成，配置: {self.config['name']}")
    
    def _detect_system_memory(self) -> int:
        """检测系统内存"""
        total_memory = psutil.virtual_memory().total / (1024 * 1024)
        return int(total_memory)
    
    def _select_optimal_config(self) -> Dict:
        """根据系统资源选择最优配置"""
        configs = [
            {
                'name': '入门级',
                'memory_threshold': 4000,
                'model': 'mini',
                'reranker': 'rule_based',
                'batch_size': 16,
                'max_candidates': 100
            },
            {
                'name': '标准级', 
                'memory_threshold': 8000,
                'model': 'bge_small',
                'reranker': 'hybrid',
                'batch_size': 32,
                'max_candidates': 500
            },
            {
                'name': '高性能',
                'memory_threshold': 16000,
                'model': 'multilingual',
                'reranker': 'ml_based',
                'batch_size': 64,
                'max_candidates': 1000
            }
        ]
        
        # 选择适合的配置
        for config in reversed(configs):
            if self.system_memory >= config['memory_threshold']:
                self.batch_processor.batch_size = config['batch_size']
                return config
        
        # 默认返回最低配置
        return configs[0]
    
    def rerank(self, query: str, candidates: List[Document], top_k: int = 10) -> List[RerankResult]:
        """执行CPU优化的重排"""
        logger.info(f"🚀 执行{self.config['name']}重排配置")
        logger.info(f"   查询: {query[:50]}...")
        logger.info(f"   候选文档数: {len(candidates)}")
        
        # 根据配置选择重排策略
        strategy = self.config['reranker']
        
        if strategy == 'rule_based':
            return self.rule_reranker.rerank(query, candidates[:self.config['max_candidates']], top_k)
        elif strategy == 'ml_based':
            return self.ml_reranker.rerank(query, candidates[:self.config['max_candidates']], top_k)
        else:  # hybrid混合策略
            return self._hybrid_rerank(query, candidates[:self.config['max_candidates']], top_k)
    
    def _hybrid_rerank(self, query: str, candidates: List[Document], top_k: int) -> List[RerankResult]:
        """混合重排策略"""
        # 第一阶段：规则过滤
        intermediate_results = self.rule_reranker.rerank(
            query, candidates, top_k=min(100, len(candidates))
        )
        
        # 第二阶段：ML精排
        filtered_docs = [
            Document(result.doc_id, result.content, {'initial_score': result.score})
            for result in intermediate_results
        ]
        
        return self.ml_reranker.rerank(query, filtered_docs, top_k)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics_history = []
    
    def monitor_execution(self, func, *args, **kwargs):
        """监控函数执行性能"""
        # 内存监控
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # 时间监控
        start_time = time.time()
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 记录指标
        execution_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_used = final_memory - initial_memory
        
        metrics = {
            'execution_time': execution_time,
            'memory_used_mb': memory_used,
            'peak_memory_mb': final_memory,
            'timestamp': time.time()
        }
        
        self.metrics_history.append(metrics)
        return result, metrics
    
    def get_performance_summary(self):
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        times = [m['execution_time'] for m in self.metrics_history]
        memories = [m['memory_used_mb'] for m in self.metrics_history]
        
        return {
            'avg_execution_time': np.mean(times),
            'max_execution_time': np.max(times),
            'avg_memory_usage': np.mean(memories),
            'max_memory_usage': np.max(memories),
            'total_executions': len(self.metrics_history)
        }

def create_sample_data(num_documents: int = 100) -> List[Document]:
    """创建示例数据"""
    sample_contents = [
        "Python是一种高级编程语言，语法简洁易读，适合初学者学习",
        "Java是面向对象的编程语言，具有跨平台特性，广泛应用企业开发",
        "人工智能是计算机科学的重要分支，致力于创造智能机器系统",
        "机器学习是实现人工智能的核心技术，使计算机能够从数据中学习",
        "深度学习是机器学习的子领域，使用神经网络模拟人脑学习过程",
        "TensorFlow是Google开发的开源机器学习框架，功能强大易用",
        "PyTorch是Facebook开发的深度学习框架，深受研究者喜爱",
        "数据分析是从大量数据中提取有价值信息的过程和技术",
        "云计算提供按需的计算资源共享池，包括服务器、存储、网络等",
        "区块链是一种分布式账本技术，具有去中心化和不可篡改的特点"
    ]
    
    documents = []
    for i in range(num_documents):
        # 循环使用样本内容并添加变化
        base_content = sample_contents[i % len(sample_contents)]
        # 添加一些变化使内容更丰富
        variations = [
            f"{base_content} 这是非常重要的技术概念。",
            f"{base_content} 在现代技术发展中扮演关键角色。",
            f"{base_content} 有着广泛的应用前景。"
        ]
        content = variations[(i // len(sample_contents)) % len(variations)]
        
        # 添加随机特征
        features = {
            'popularity': np.random.uniform(0.3, 1.0),
            'recency': np.random.uniform(0.1, 1.0)
        }
        
        documents.append(Document(doc_id=i, content=content, features=features))
    
    return documents

def demo_cpu_reranking():
    """CPU重排优化演示"""
    logger.info("🚀 启动CPU-only重排优化演示")
    logger.info(f"💻 系统内存: {psutil.virtual_memory().total / (1024**3):.1f}GB")
    
    # 创建演示数据
    sample_documents = create_sample_data(200)
    logger.info(f"📄 准备了 {len(sample_documents)} 个示例文档")
    
    # 创建性能监控器
    monitor = PerformanceMonitor()
    
    # 测试不同配置
    test_configs = ['入门级', '标准级', '高性能']
    test_queries = [
        "Python编程语言的特点是什么？",
        "什么是人工智能技术？",
        "机器学习和深度学习有什么区别？"
    ]
    
    for config_name in test_configs:
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 测试 {config_name} 配置")
        logger.info(f"{'='*60}")
        
        # 创建对应配置的流水线
        pipeline = CPURerankingPipeline()
        
        # 临时修改配置以测试不同策略
        if config_name == '入门级':
            pipeline.config['reranker'] = 'rule_based'
        elif config_name == '标准级':
            pipeline.config['reranker'] = 'hybrid'
        else:  # 高性能
            pipeline.config['reranker'] = 'ml_based'
        
        total_time = 0
        total_memory = 0
        
        for i, query in enumerate(test_queries):
            # 监控执行性能
            results, metrics = monitor.monitor_execution(
                pipeline.rerank, query, sample_documents, 10
            )
            
            total_time += metrics['execution_time']
            total_memory += metrics['memory_used_mb']
            
            logger.info(f"\n查询 {i+1}: {query}")
            logger.info(f"处理时间: {metrics['execution_time']:.4f}秒")
            logger.info(f"内存使用: {metrics['memory_used_mb']:.1f}MB")
            logger.info(f"返回结果数: {len(results)}")
            
            # 显示前3个结果
            logger.info("Top 3 结果:")
            for result in results[:3]:
                logger.info(f"  {result.rank}. [分数:{result.score:.3f}] {result.content[:60]}...")
        
        avg_time = total_time / len(test_queries)
        avg_memory = total_memory / len(test_queries)
        logger.info(f"\n📈 {config_name} 配置汇总:")
        logger.info(f"   平均处理时间: {avg_time:.4f}秒")
        logger.info(f"   平均内存使用: {avg_memory:.1f}MB")
    
    # 输出总体性能报告
    summary = monitor.get_performance_summary()
    logger.info(f"\n{'='*60}")
    logger.info("🏆 CPU重排优化演示完成!")
    logger.info(f"📊 总体性能摘要:")
    logger.info(f"   总执行次数: {summary['total_executions']}")
    logger.info(f"   平均执行时间: {summary['avg_execution_time']:.4f}秒")
    logger.info(f"   最大内存使用: {summary['max_memory_usage']:.1f}MB")
    logger.info(f"   平均内存使用: {summary['avg_memory_usage']:.1f}MB")
    logger.info(f"{'='*60}")
    
    # 实用建议
    logger.info(f"\n💡 实用建议:")
    logger.info(f"   • 内存≤4GB: 推荐入门级配置(规则重排)")
    logger.info(f"   • 内存4-8GB: 推荐标准级配置(混合重排)") 
    logger.info(f"   • 内存≥8GB: 可使用高性能配置(ML重排)")
    logger.info(f"   • 关键是实用性而非理论最优!")

if __name__ == "__main__":
    demo_cpu_reranking()