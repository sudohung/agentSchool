"""
工业级重排优化实战演示
Industry-Grade Reranking Optimization Demo
"""

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import faiss
import time
import logging
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果数据结构"""
    doc_id: int
    content: str
    initial_score: float
    features: Dict[str, float]

@dataclass  
class RerankRequest:
    """重排请求数据结构"""
    query: str
    candidates: List[SearchResult]
    context: Dict[str, Any] = None

class BaseReranker(ABC):
    """重排器基类"""
    
    @abstractmethod
    def rerank(self, request: RerankRequest) -> List[SearchResult]:
        pass

class PointwiseReranker(BaseReranker):
    """Pointwise重排器 - 工业界最常用"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)
        logger.info(f"✅ Pointwise重排器初始化完成: {model_name}")
    
    def rerank(self, request: RerankRequest) -> List[SearchResult]:
        """基于交叉编码器的pointwise重排"""
        if not request.candidates:
            return []
        
        # 构建查询-文档对
        query_doc_pairs = [[request.query, candidate.content] 
                          for candidate in request.candidates]
        
        # 预测相关性分数
        start_time = time.time()
        scores = self.model.predict(query_doc_pairs, show_progress_bar=False)
        inference_time = time.time() - start_time
        
        # 更新分数并排序
        reranked_candidates = []
        for i, (candidate, score) in enumerate(zip(request.candidates, scores)):
            new_candidate = SearchResult(
                doc_id=candidate.doc_id,
                content=candidate.content,
                initial_score=float(score),
                features={**candidate.features, 'cross_encoder_score': float(score)}
            )
            reranked_candidates.append(new_candidate)
        
        # 按分数降序排列
        reranked_candidates.sort(key=lambda x: x.initial_score, reverse=True)
        
        logger.info(f"🔄 Pointwise重排完成，处理{len(reranked_candidates)}个候选，耗时{inference_time:.4f}秒")
        return reranked_candidates

class EnsembleReranker(BaseReranker):
    """集成重排器 - 多模型融合"""
    
    def __init__(self):
        self.pointwise_reranker = PointwiseReranker()
        self.semantic_reranker = SemanticReranker()
        self.feature_based_reranker = FeatureBasedReranker()
        logger.info("✅ 集成重排器初始化完成")
    
    def rerank(self, request: RerankRequest) -> List[SearchResult]:
        """多模型集成重排"""
        # 获取各个模型的排序结果
        pointwise_results = self.pointwise_reranker.rerank(request)
        semantic_results = self.semantic_reranker.rerank(request)
        feature_results = self.feature_based_reranker.rerank(request)
        
        # 融合多个排序结果
        fused_results = self._fuse_rankings([
            pointwise_results,
            semantic_results, 
            feature_results
        ], weights=[0.5, 0.3, 0.2])
        
        logger.info(f"🔄 集成重排完成，融合了3个模型的结果")
        return fused_results
    
    def _fuse_rankings(self, rankings_list: List[List[SearchResult]], 
                      weights: List[float]) -> List[SearchResult]:
        """融合多个排序结果"""
        if not rankings_list or not weights:
            return []
        
        # 收集所有文档ID
        all_doc_ids = set()
        for ranking in rankings_list:
            all_doc_ids.update(candidate.doc_id for candidate in ranking)
        
        # 计算加权融合分数
        fused_scores = {}
        doc_mapping = {}
        
        for ranking, weight in zip(rankings_list, weights):
            ranking_length = len(ranking)
            for rank_pos, candidate in enumerate(ranking):
                doc_id = candidate.doc_id
                # 使用排名倒数作为分数（排名越前分数越高）
                score = (ranking_length - rank_pos) * weight
                fused_scores[doc_id] = fused_scores.get(doc_id, 0) + score
                doc_mapping[doc_id] = candidate
        
        # 按融合分数排序
        sorted_doc_ids = sorted(fused_scores.keys(), 
                               key=lambda x: fused_scores[x], 
                               reverse=True)
        
        # 构建最终结果
        final_results = [doc_mapping[doc_id] for doc_id in sorted_doc_ids]
        return final_results

class SemanticReranker(BaseReranker):
    """语义重排器"""
    
    def __init__(self):
        self.encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        logger.info("✅ 语义重排器初始化完成")
    
    def rerank(self, request: RerankRequest) -> List[SearchResult]:
        """基于语义相似度的重排"""
        if not request.candidates:
            return []
        
        # 编码查询和候选文档
        query_embedding = self.encoder.encode([request.query])
        doc_embeddings = self.encoder.encode([c.content for c in request.candidates])
        
        # 计算余弦相似度
        similarities = np.dot(doc_embeddings, query_embedding.T).flatten()
        
        # 更新候选结果
        reranked_candidates = []
        for i, (candidate, similarity) in enumerate(zip(request.candidates, similarities)):
            new_candidate = SearchResult(
                doc_id=candidate.doc_id,
                content=candidate.content,
                initial_score=float(similarity),
                features={**candidate.features, 'semantic_similarity': float(similarity)}
            )
            reranked_candidates.append(new_candidate)
        
        # 按相似度排序
        reranked_candidates.sort(key=lambda x: x.initial_score, reverse=True)
        
        return reranked_candidates

class FeatureBasedReranker(BaseReranker):
    """基于特征的重排器"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        logger.info("✅ 特征重排器初始化完成")
    
    def train(self, training_data: List[Tuple[RerankRequest, List[int]]]):
        """训练特征重排模型"""
        logger.info("🏋️ 开始训练特征重排模型...")
        
        X, y = [], []
        
        for request, ground_truth_ranks in training_data:
            # 为每个候选文档提取特征
            for i, candidate in enumerate(request.candidates):
                features = self._extract_features(request.query, candidate)
                X.append(list(features.values()))
                
                # 计算标签（排名位置的倒数）
                rank_position = ground_truth_ranks.index(candidate.doc_id) \
                    if candidate.doc_id in ground_truth_ranks else len(ground_truth_ranks)
                y.append(1.0 / (rank_position + 1))  # 转换为分数
        
        if X and y:
            # 标准化特征
            X_scaled = self.scaler.fit_transform(X)
            # 训练模型
            self.model.fit(X_scaled, y)
            self.is_trained = True
            logger.info("✅ 特征重排模型训练完成")
        else:
            logger.warning("⚠️ 训练数据不足，无法训练模型")
    
    def rerank(self, request: RerankRequest) -> List[SearchResult]:
        """基于机器学习特征的重排"""
        if not request.candidates:
            return []
        
        if not self.is_trained:
            logger.warning("⚠️ 模型未训练，使用默认排序")
            return request.candidates
        
        # 提取特征
        features_list = []
        for candidate in request.candidates:
            features = self._extract_features(request.query, candidate)
            features_list.append(list(features.values()))
        
        # 预测分数
        features_scaled = self.scaler.transform(features_list)
        predicted_scores = self.model.predict(features_scaled)
        
        # 更新候选结果
        reranked_candidates = []
        for i, (candidate, score) in enumerate(zip(request.candidates, predicted_scores)):
            new_candidate = SearchResult(
                doc_id=candidate.doc_id,
                content=candidate.content,
                initial_score=float(score),
                features={**candidate.features, 'ml_score': float(score)}
            )
            reranked_candidates.append(new_candidate)
        
        # 按预测分数排序
        reranked_candidates.sort(key=lambda x: x.initial_score, reverse=True)
        
        return reranked_candidates
    
    def _extract_features(self, query: str, candidate: SearchResult) -> Dict[str, float]:
        """提取重排特征"""
        features = {}
        
        # 文本长度特征
        features['query_length'] = len(query)
        features['doc_length'] = len(candidate.content)
        features['length_ratio'] = len(candidate.content) / (len(query) + 1)
        
        # 词汇匹配特征
        query_words = set(query.lower().split())
        doc_words = set(candidate.content.lower().split())
        features['word_overlap'] = len(query_words & doc_words)
        features['overlap_ratio'] = len(query_words & doc_words) / (len(query_words) + 1)
        
        # BM25启发式特征
        features['bm25_like'] = self._bm25_heuristic(query, candidate.content)
        
        # 原始分数特征
        features['initial_score'] = candidate.initial_score
        
        # 上下文特征（如果有的话）
        if candidate.features:
            features.update(candidate.features)
        
        return features
    
    def _bm25_heuristic(self, query: str, doc: str) -> float:
        """BM25启发式计算"""
        query_terms = query.lower().split()
        doc_terms = doc.lower().split()
        
        k1, b = 1.2, 0.75
        avg_doc_len = len(doc_terms)
        doc_len = len(doc_terms)
        
        score = 0
        for term in query_terms:
            tf = doc_terms.count(term)
            if tf > 0:
                idf = np.log((1000 - tf + 0.5) / (tf + 0.5))
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
                score += idf * numerator / denominator
        
        return score

class OnlineLearningReranker(BaseReranker):
    """在线学习重排器"""
    
    def __init__(self, base_reranker: BaseReranker):
        self.base_reranker = base_reranker
        self.feedback_buffer = []
        self.update_threshold = 100  # 收集100个反馈后更新
        logger.info("✅ 在线学习重排器初始化完成")
    
    def rerank(self, request: RerankRequest) -> List[SearchResult]:
        """带在线学习的重排"""
        # 使用基础重排器
        results = self.base_reranker.rerank(request)
        
        # 记录用于在线学习的信息
        self._record_interaction(request, results)
        
        return results
    
    def record_feedback(self, query_id: str, clicked_doc_ids: List[int]):
        """记录用户反馈"""
        self.feedback_buffer.append({
            'query_id': query_id,
            'clicked_docs': clicked_doc_ids,
            'timestamp': time.time()
        })
        
        # 检查是否需要更新模型
        if len(self.feedback_buffer) >= self.update_threshold:
            self._update_model()
    
    def _record_interaction(self, request: RerankRequest, results: List[SearchResult]):
        """记录交互数据"""
        # 这里可以记录更详细的交互信息用于后续学习
        pass
    
    def _update_model(self):
        """更新重排模型"""
        logger.info(f"🔄 基于{len(self.feedback_buffer)}个反馈更新模型...")
        # 实际实现中这里会使用在线学习算法更新模型参数
        self.feedback_buffer = []  # 清空缓冲区

class RerankingPipeline:
    """重排流水线 - 工业界标准架构"""
    
    def __init__(self):
        # 构建多阶段重排流水线
        self.pipeline = [
            ('pointwise', PointwiseReranker()),
            ('ensemble', EnsembleReranker()),
            ('online_learning', OnlineLearningReranker(EnsembleReranker()))
        ]
        logger.info("✅ 重排流水线初始化完成")
    
    def rerank_pipeline(self, request: RerankRequest, stage: str = 'production') -> List[SearchResult]:
        """执行重排流水线"""
        logger.info(f"🚀 执行{stage}重排流水线...")
        
        current_candidates = request.candidates
        timing_info = {}
        
        # 根据阶段选择合适的重排器
        if stage == 'quick':
            reranker = self.pipeline[0][1]  # 快速模式：仅pointwise
        elif stage == 'balanced':
            reranker = self.pipeline[1][1]  # 平衡模式：集成重排
        else:  # production模式
            reranker = self.pipeline[2][1]  # 生产模式：在线学习
        
        start_time = time.time()
        final_results = reranker.rerank(RerankRequest(
            query=request.query,
            candidates=current_candidates,
            context=request.context
        ))
        total_time = time.time() - start_time
        
        timing_info['total_time'] = total_time
        logger.info(f"✅ 重排流水线执行完成，总耗时: {total_time:.4f}秒")
        
        return final_results, timing_info

class PerformanceEvaluator:
    """性能评估器"""
    
    def __init__(self):
        self.metrics_history = []
    
    def evaluate_reranking(self, ground_truth: List[int], predictions: List[SearchResult]) -> Dict[str, float]:
        """评估重排性能"""
        # 提取预测的文档ID顺序
        predicted_order = [result.doc_id for result in predictions]
        
        # 计算各种指标
        metrics = {
            'ndcg': self._calculate_ndcg(ground_truth, predicted_order),
            'precision_at_k': self._calculate_precision_at_k(ground_truth, predicted_order, k=5),
            'mrr': self._calculate_mrr(ground_truth, predicted_order),
            'map': self._calculate_map(ground_truth, predicted_order)
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def _calculate_ndcg(self, ground_truth: List[int], predicted: List[int], k=10) -> float:
        """计算NDCG"""
        def dcg_score(items, relevance_dict, k):
            return sum((relevance_dict.get(item, 0) / np.log2(i + 2)) 
                      for i, item in enumerate(items[:k]))
        
        # 构建相关性字典（ground truth中前面的更相关）
        relevance = {doc_id: len(ground_truth) - i 
                    for i, doc_id in enumerate(ground_truth)}
        
        # 计算DCG和IDCG
        dcg = dcg_score(predicted, relevance, k)
        ideal_order = sorted(ground_truth, key=lambda x: relevance.get(x, 0), reverse=True)
        idcg = dcg_score(ideal_order, relevance, k)
        
        return dcg / idcg if idcg > 0 else 0
    
    def _calculate_precision_at_k(self, ground_truth: List[int], predicted: List[int], k=5) -> float:
        """计算Precision@K"""
        relevant_items = set(ground_truth[:k])
        predicted_items = set(predicted[:k])
        return len(relevant_items & predicted_items) / k if k > 0 else 0
    
    def _calculate_mrr(self, ground_truth: List[int], predicted: List[int]) -> float:
        """计算MRR"""
        for i, pred_item in enumerate(predicted):
            if pred_item in ground_truth:
                return 1.0 / (i + 1)
        return 0.0
    
    def _calculate_map(self, ground_truth: List[int], predicted: List[int]) -> float:
        """计算MAP"""
        relevant_items = set(ground_truth)
        ap_sum = 0.0
        hits = 0
        
        for i, pred_item in enumerate(predicted):
            if pred_item in relevant_items:
                hits += 1
                ap_sum += hits / (i + 1)
        
        return ap_sum / len(relevant_items) if relevant_items else 0

def demo_industry_reranking():
    """工业级重排优化演示"""
    logger.info("🚀 启动工业级重排优化演示")
    
    # 准备演示数据
    sample_documents = [
        SearchResult(0, "Python是一种高级编程语言，语法简洁易读", 0.8, {'popularity': 0.9}),
        SearchResult(1, "Java是面向对象的编程语言，具有跨平台特性", 0.7, {'popularity': 0.8}),
        SearchResult(2, "人工智能是计算机科学的重要分支领域", 0.9, {'popularity': 0.95}),
        SearchResult(3, "机器学习是实现人工智能的核心技术方法", 0.85, {'popularity': 0.85}),
        SearchResult(4, "深度学习是机器学习的一个重要子领域", 0.82, {'popularity': 0.8}),
        SearchResult(5, "TensorFlow是Google开发的机器学习框架", 0.78, {'popularity': 0.75})
    ]
    
    # 创建重排流水线
    pipeline = RerankingPipeline()
    evaluator = PerformanceEvaluator()
    
    # 测试查询
    test_cases = [
        {
            'query': "Python编程语言的特点",
            'candidates': sample_documents[:4],
            'ground_truth': [0, 1, 2, 3]  # 理想排序
        },
        {
            'query': "什么是人工智能？",
            'candidates': sample_documents[2:],
            'ground_truth': [2, 3, 4, 5]  # 理想排序
        }
    ]
    
    # 演示不同阶段的重排效果
    stages = ['quick', 'balanced', 'production']
    
    for stage in stages:
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 {stage.upper()} 阶段重排演示")
        logger.info(f"{'='*50}")
        
        total_improvement = 0
        
        for i, test_case in enumerate(test_cases):
            request = RerankRequest(
                query=test_case['query'],
                candidates=test_case['candidates']
            )
            
            # 执行重排
            results, timing = pipeline.rerank_pipeline(request, stage=stage)
            
            # 评估效果
            metrics = evaluator.evaluate_reranking(test_case['ground_truth'], results)
            
            logger.info(f"\n测试用例 {i+1}: {test_case['query']}")
            logger.info(f"处理时间: {timing['total_time']:.4f}秒")
            logger.info(f"NDCG@10: {metrics['ndcg']:.4f}")
            logger.info(f"Precision@5: {metrics['precision_at_k']:.4f}")
            logger.info(f"MRR: {metrics['mrr']:.4f}")
            logger.info(f"MAP: {metrics['map']:.4f}")
            
            # 显示排序结果
            logger.info("排序结果:")
            for j, result in enumerate(results[:3]):
                logger.info(f"  {j+1}. [分数: {result.initial_score:.3f}] {result.content}")
            
            total_improvement += metrics['ndcg']
        
        avg_improvement = total_improvement / len(test_cases)
        logger.info(f"\n📈 {stage} 阶段平均NDCG: {avg_improvement:.4f}")
    
    # 总结性能对比
    logger.info(f"\n{'='*60}")
    logger.info("🏆 工业级重排优化演示完成!")
    logger.info("💡 不同重排策略的适用场景:")
    logger.info("   • Quick: 实时性要求高的场景")
    logger.info("   • Balanced: 平衡效果和性能的通用场景") 
    logger.info("   • Production: 对效果要求极高的生产环境")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    demo_industry_reranking()