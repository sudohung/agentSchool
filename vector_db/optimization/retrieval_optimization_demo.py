"""
向量数据库检索可靠性优化实战示例
Practical Examples for Improving Vector Database Retrieval Reliability
"""

import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import time
import re
from collections import defaultdict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrievalOptimizer:
    """检索优化器主类"""
    
    def __init__(self):
        self.models = {}
        self.indexes = {}
        self.quality_metrics = {}
        
    def load_models(self):
        """加载各种嵌入模型进行对比测试"""
        logger.info("🚀 加载嵌入模型...")
        
        model_configs = [
            ('multilingual', 'paraphrase-multilingual-MiniLM-L12-v2'),
            ('english', 'all-MiniLM-L6-v2'),
            ('chinese', 'bge-small-zh-v1.5')
        ]
        
        for name, model_path in model_configs:
            try:
                self.models[name] = SentenceTransformer(model_path)
                logger.info(f"✅ {name} 模型加载成功")
            except Exception as e:
                logger.warning(f"❌ {name} 模型加载失败: {e}")

class ModelComparisonTester:
    """模型对比测试器"""
    
    def __init__(self):
        self.optimizer = RetrievalOptimizer()
        self.test_data = []
        
    def prepare_test_data(self):
        """准备测试数据"""
        self.test_data = [
            # 技术类查询
            ("Python编程语言的特点", 
             ["Python是一种解释型、面向对象的高级编程语言",
              "Python语法简洁易读，适合初学者学习",
              "Python拥有丰富的第三方库生态系统"]),
            
            ("机器学习算法", 
             ["机器学习是人工智能的核心技术",
              "常见的机器学习算法包括决策树、随机森林、神经网络",
              "监督学习和无监督学习是机器学习的主要分类"]),
            
            ("深度学习框架", 
             ["TensorFlow是Google开发的深度学习框架",
              "PyTorch由Facebook开发，广受研究者欢迎",
              "Keras是高层神经网络API，易于使用"]),
            
            # 日常生活类查询  
            ("健康饮食建议",
             ["均衡饮食包括蛋白质、碳水化合物、脂肪的合理搭配",
              "多吃蔬菜水果，少吃油炸食品",
              "保持规律的用餐时间和适量运动"]),
            
            ("旅游景点推荐",
             ["北京故宫是中国明清两代的皇家宫殿",
              "西湖位于杭州，以秀丽的湖光山色闻名",
              "长城是中国古代的军事防御工程"])
        ]
        
        logger.info(f"✅ 准备了 {len(self.test_data)} 组测试数据")
    
    def compare_models(self):
        """对比不同模型的性能"""
        logger.info("🔬 开始模型性能对比测试...")
        
        results = {}
        
        for model_name, model in self.optimizer.models.items():
            logger.info(f"测试模型: {model_name}")
            
            model_results = {
                'encoding_times': [],
                'accuracies': [],
                'qualities': []
            }
            
            for query, expected_docs in self.test_data:
                # 编码时间测试
                start_time = time.time()
                query_embedding = model.encode([query])
                encoding_time = time.time() - start_time
                model_results['encoding_times'].append(encoding_time)
                
                # 质量评估
                doc_embeddings = model.encode(expected_docs)
                similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
                
                # 计算准确性（假设最相关的应该是第一个文档）
                accuracy = similarities[0] if len(similarities) > 0 else 0
                model_results['accuracies'].append(accuracy)
                
                # 质量分数计算
                quality_score = self._calculate_quality_score(similarities)
                model_results['qualities'].append(quality_score)
            
            # 计算平均值
            results[model_name] = {
                'avg_encoding_time': np.mean(model_results['encoding_times']),
                'avg_accuracy': np.mean(model_results['accuracies']),
                'avg_quality': np.mean(model_results['qualities']),
                'std_accuracy': np.std(model_results['accuracies'])
            }
            
            logger.info(f"  平均编码时间: {results[model_name]['avg_encoding_time']:.4f}s")
            logger.info(f"  平均准确率: {results[model_name]['avg_accuracy']:.3f}")
            logger.info(f"  平均质量分: {results[model_name]['avg_quality']:.3f}")
            logger.info("-" * 40)
        
        return results
    
    def _calculate_quality_score(self, similarities):
        """计算质量分数"""
        if len(similarities) < 2:
            return 1.0
        
        # 质量评估：相似度应该有适当的区分度
        mean_sim = np.mean(similarities)
        std_sim = np.std(similarities)
        
        # 理想情况下，相似度既不过于集中也不过于分散
        quality = 1.0 - abs(mean_sim - 0.5) - std_sim
        return max(0, min(1, quality))

class AdvancedPreprocessor:
    """高级文本预处理器"""
    
    def __init__(self):
        self.stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '也', '很', '还'}
        self.synonym_map = {
            '人工智能': ['AI', '人工智慧'],
            '机器学习': ['ML', '深度学习'],
            '编程': ['写代码', '软件开发', '程序设计'],
            '数据': ['资料', '信息'],
            '算法': ['演算法']
        }
    
    def preprocess_batch(self, texts):
        """批量预处理文本"""
        processed_texts = []
        for text in texts:
            processed = self.preprocess_text(text)
            processed_texts.append(processed)
        return processed_texts
    
    def preprocess_text(self, text):
        """完整的文本预处理流程"""
        # 1. 基础清理
        text = self._basic_clean(text)
        
        # 2. 分词和过滤
        tokens = self._tokenize_and_filter(text)
        
        # 3. 同义词扩展
        expanded_text = self._expand_synonyms(' '.join(tokens))
        
        # 4. 标准化处理
        normalized_text = self._normalize_entities(expanded_text)
        
        return normalized_text.strip()
    
    def _basic_clean(self, text):
        """基础文本清理"""
        # 统一空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        # 处理标点符号（保留中英文标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', ' ', text)
        return text
    
    def _tokenize_and_filter(self, text):
        """分词和停用词过滤"""
        # 简单分词（实际项目建议使用jieba等专业工具）
        tokens = text.split()
        
        # 过滤停用词和过短词汇
        filtered_tokens = [
            token for token in tokens 
            if len(token.strip()) > 1 and token not in self.stop_words
        ]
        
        return filtered_tokens
    
    def _expand_synonyms(self, text):
        """同义词扩展"""
        for primary_term, synonyms in self.synonym_map.items():
            if primary_term in text:
                # 添加同义词到文本中
                synonym_str = ' '.join(synonyms)
                text = text.replace(primary_term, f"{primary_term} {synonym_str}")
        return text
    
    def _normalize_entities(self, text):
        """实体标准化"""
        # 日期格式标准化
        text = re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1-\2-\3', text)
        # 数字格式标准化
        text = re.sub(r'(\d+(?:\.\d+)?)\s*(?:个|只|条|份|位)', r'\1', text)
        return text

class HybridRetriever:
    """混合检索器"""
    
    def __init__(self, preprocessor=None):
        self.preprocessor = preprocessor or AdvancedPreprocessor()
        self.vector_model = None
        self.tfidf_vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
        self.vector_index = None
        self.tfidf_index = None
        self.documents = []
        
    def initialize_models(self):
        """初始化模型"""
        try:
            self.vector_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("✅ 向量模型初始化成功")
        except Exception as e:
            logger.error(f"❌ 向量模型初始化失败: {e}")
            return False
        return True
    
    def build_indexes(self, documents):
        """构建混合索引"""
        logger.info("🏗️ 构建混合检索索引...")
        self.documents = documents
        
        # 1. 文本预处理
        processed_docs = self.preprocessor.preprocess_batch(documents)
        
        # 2. 构建向量索引
        if self._build_vector_index(processed_docs):
            logger.info("✅ 向量索引构建完成")
        
        # 3. 构建TF-IDF索引
        if self._build_tfidf_index(documents):
            logger.info("✅ TF-IDF索引构建完成")
        
        logger.info(f"✅ 总共索引了 {len(documents)} 个文档")
    
    def _build_vector_index(self, documents):
        """构建向量索引"""
        try:
            embeddings = self.vector_model.encode(documents, show_progress_bar=True)
            dimension = embeddings.shape[1]
            
            # 使用IVF索引提高搜索效率
            quantizer = faiss.IndexFlatL2(dimension)
            self.vector_index = faiss.IndexIVFFlat(quantizer, dimension, 100)
            self.vector_index.train(embeddings.astype('float32'))
            self.vector_index.add(embeddings.astype('float32'))
            
            return True
        except Exception as e:
            logger.error(f"❌ 向量索引构建失败: {e}")
            return False
    
    def _build_tfidf_index(self, documents):
        """构建TF-IDF索引"""
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            self.tfidf_index = tfidf_matrix
            return True
        except Exception as e:
            logger.error(f"❌ TF-IDF索引构建失败: {e}")
            return False
    
    def hybrid_search(self, query, k=10, weights=None):
        """混合搜索"""
        if weights is None:
            weights = {'vector': 0.6, 'tfidf': 0.4}
        
        # 预处理查询
        processed_query = self.preprocessor.preprocess_text(query)
        
        # 执行不同类型的搜索
        vector_results = self._vector_search(processed_query, k*2)
        tfidf_results = self._tfidf_search(query, k*2)
        
        # 融合结果
        final_results = self._combine_results(
            vector_results, tfidf_results, weights, k
        )
        
        return final_results
    
    def _vector_search(self, query, k):
        """向量搜索"""
        try:
            query_vector = self.vector_model.encode([query])
            distances, indices = self.vector_index.search(
                query_vector.astype('float32'), k
            )
            
            results = []
            for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
                if idx < len(self.documents):  # 确保索引有效
                    similarity = 1.0 / (1.0 + dist)
                    results.append((similarity, idx))
            
            return results
        except Exception as e:
            logger.error(f"❌ 向量搜索失败: {e}")
            return []
    
    def _tfidf_search(self, query, k):
        """TF-IDF搜索"""
        try:
            query_vector = self.tfidf_vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, self.tfidf_index).flatten()
            
            # 获取top-k结果
            top_indices = similarities.argsort()[-k:][::-1]
            results = [(similarities[idx], idx) for idx in top_indices 
                      if similarities[idx] > 0]
            
            return results
        except Exception as e:
            logger.error(f"❌ TF-IDF搜索失败: {e}")
            return []
    
    def _combine_results(self, vector_results, tfidf_results, weights, k):
        """融合不同搜索结果"""
        # 收集所有文档ID和对应的分数
        combined_scores = defaultdict(float)
        
        # 处理向量搜索结果
        for score, doc_id in vector_results:
            combined_scores[doc_id] += weights['vector'] * score
        
        # 处理TF-IDF搜索结果
        for score, doc_id in tfidf_results:
            combined_scores[doc_id] += weights['tfidf'] * score
        
        # 排序并返回top-k
        sorted_results = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:k]
        
        # 转换为(分数, 文档内容)格式
        final_results = [
            (score, self.documents[doc_id]) 
            for doc_id, score in sorted_results
            if doc_id < len(self.documents)
        ]
        
        return final_results

class RetrievalQualityEvaluator:
    """检索质量评估器"""
    
    def __init__(self):
        self.metrics_history = []
    
    def evaluate_retrieval(self, query, results, ground_truth=None):
        """评估单次检索的质量"""
        evaluation = {
            'query': query,
            'result_count': len(results),
            'timestamp': time.time()
        }
        
        # 如果有标准答案，计算准确率指标
        if ground_truth:
            precision, recall = self._calculate_precision_recall(results, ground_truth)
            evaluation.update({
                'precision': precision,
                'recall': recall,
                'f1_score': 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            })
        
        # 计算结果多样性
        diversity_score = self._calculate_diversity(results)
        evaluation['diversity'] = diversity_score
        
        # 计算分数分布
        if results:
            scores = [score for score, _ in results]
            evaluation.update({
                'avg_score': np.mean(scores),
                'score_std': np.std(scores),
                'score_range': max(scores) - min(scores)
            })
        
        self.metrics_history.append(evaluation)
        return evaluation
    
    def _calculate_precision_recall(self, results, ground_truth):
        """计算精确率和召回率"""
        result_docs = [doc for _, doc in results]
        truth_set = set(ground_truth)
        result_set = set(result_docs)
        
        intersection = truth_set & result_set
        precision = len(intersection) / len(result_set) if result_set else 0
        recall = len(intersection) / len(truth_set) if truth_set else 0
        
        return precision, recall
    
    def _calculate_diversity(self, results):
        """计算结果多样性"""
        if len(results) < 2:
            return 1.0
        
        # 简单的多样性计算：基于分数的标准差
        scores = [score for score, _ in results]
        score_std = np.std(scores)
        
        # 标准化到0-1范围
        max_possible_std = 1.0  # 假设分数范围是0-1
        diversity = min(1.0, score_std / max_possible_std)
        
        return diversity
    
    def get_overall_metrics(self):
        """获取整体性能指标"""
        if not self.metrics_history:
            return {}
        
        metrics_summary = {
            'total_queries': len(self.metrics_history),
            'avg_result_count': np.mean([m['result_count'] for m in self.metrics_history])
        }
        
        # 计算有标准答案的查询的平均指标
        evaluated_queries = [m for m in self.metrics_history if 'precision' in m]
        if evaluated_queries:
            metrics_summary.update({
                'avg_precision': np.mean([m['precision'] for m in evaluated_queries]),
                'avg_recall': np.mean([m['recall'] for m in evaluated_queries]),
                'avg_f1': np.mean([m['f1_score'] for m in evaluated_queries]),
                'avg_diversity': np.mean([m['diversity'] for m in self.metrics_history])
            })
        
        return metrics_summary

def run_optimization_demo():
    """运行优化演示"""
    logger.info("🚀 启动检索可靠性优化演示")
    
    # 1. 模型对比测试
    tester = ModelComparisonTester()
    tester.prepare_test_data()
    model_results = tester.compare_models()
    
    logger.info("🏆 模型性能对比结果:")
    for model_name, metrics in model_results.items():
        logger.info(f"{model_name}: 准确率={metrics['avg_accuracy']:.3f}, "
                   f"质量分={metrics['avg_quality']:.3f}")
    
    # 2. 混合检索演示
    logger.info("\n🔍 混合检索演示:")
    
    # 准备演示数据
    demo_documents = [
        "Python是一种高级编程语言，以其简洁易读的语法而闻名",
        "Java是一种面向对象的编程语言，具有跨平台特性",
        "人工智能是计算机科学的一个分支，致力于创造智能机器",
        "机器学习是人工智能的核心技术，使计算机能够从数据中学习",
        "深度学习是机器学习的一个子领域，使用神经网络进行学习",
        "TensorFlow是Google开发的开源机器学习框架",
        "PyTorch是Facebook开发的深度学习框架，广受研究人员欢迎"
    ]
    
    # 创建混合检索器
    hybrid_retriever = HybridRetriever()
    if hybrid_retriever.initialize_models():
        hybrid_retriever.build_indexes(demo_documents)
        
        # 测试查询
        test_queries = [
            "Python编程语言有什么特点？",
            "什么是人工智能？",
            "有哪些深度学习框架？"
        ]
        
        evaluator = RetrievalQualityEvaluator()
        
        for query in test_queries:
            logger.info(f"\n❓ 查询: {query}")
            results = hybrid_retriever.hybrid_search(query, k=3)
            
            logger.info("🎯 检索结果:")
            for i, (score, doc) in enumerate(results, 1):
                logger.info(f"  {i}. [相似度: {score:.3f}] {doc}")
            
            # 评估质量
            evaluation = evaluator.evaluate_retrieval(query, results)
            logger.info(f"📊 质量评估: 多样性={evaluation['diversity']:.3f}")
    
    # 3. 输出整体性能报告
    overall_metrics = evaluator.get_overall_metrics()
    logger.info(f"\n📈 整体性能报告:")
    for metric, value in overall_metrics.items():
        logger.info(f"  {metric}: {value:.3f}")

if __name__ == "__main__":
    run_optimization_demo()