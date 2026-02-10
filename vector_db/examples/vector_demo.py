"""
向量数据库和嵌入模型实战示例
Vector Database and Embedding Model Practical Examples
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import time

class VectorDBDemo:
    """向量数据库演示类"""
    
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """初始化嵌入模型"""
        print("🚀 初始化嵌入模型...")
        self.model = SentenceTransformer(model_name)
        print(f"✅ 模型 '{model_name}' 加载完成")
        
    def text_to_vectors(self, texts):
        """将文本转换为向量"""
        print(f"\n📝 将 {len(texts)} 条文本转换为向量...")
        start_time = time.time()
        vectors = self.model.encode(texts)
        end_time = time.time()
        
        print(f"✅ 转换完成，耗时: {end_time - start_time:.2f} 秒")
        print(f"📊 向量维度: {len(vectors[0])}")
        print(f"📊 向量数量: {len(vectors)}")
        
        return vectors
    
    def create_vector_db(self, vectors):
        """创建向量数据库"""
        print("\n🗄️ 创建向量数据库...")
        dimension = len(vectors[0])
        
        # 使用 L2 距离的平面索引
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(vectors))
        
        print(f"✅ 向量数据库创建完成")
        print(f"📊 数据库存储向量数: {index.ntotal}")
        
        return index
    
    def search_similar(self, index, query_text, texts, k=3):
        """搜索相似文本"""
        print(f"\n🔍 搜索与 '{query_text}' 相似的文本...")
        
        # 将查询文本转换为向量
        query_vector = self.model.encode([query_text])
        
        # 执行搜索
        distances, indices = index.search(np.array([query_vector]), k)
        
        print("🎯 搜索结果:")
        print("-" * 50)
        for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            print(f"{i+1}. {texts[idx]}")
            print(f"   相似度分数: {dist:.2f}")
            print()
            
        return indices[0], distances[0]

def demo_basic_usage():
    """基础使用演示"""
    print("=" * 60)
    print("📚 向量数据库基础使用演示")
    print("=" * 60)
    
    # 创建演示实例
    demo = VectorDBDemo()
    
    # 示例文本数据
    sample_texts = [
        "人工智能正在改变世界",
        "机器学习是AI的核心技术",
        "深度学习在图像识别中表现出色",
        "自然语言处理让计算机理解人类语言",
        "Python是数据科学的首选语言",
        "今天天气真好",
        "我喜欢吃苹果",
        "红富士是一种优质的苹果品种"
    ]
    
    # 转换为向量
    vectors = demo.text_to_vectors(sample_texts)
    
    # 创建向量数据库
    vector_db = demo.create_vector_db(vectors)
    
    # 执行搜索
    queries = [
        "AI技术的发展",
        "水果相关的词汇",
        "编程语言介绍"
    ]
    
    for query in queries:
        demo.search_similar(vector_db, query, sample_texts)
        print("=" * 50)

def demo_similarity_calculation():
    """相似度计算演示"""
    print("\n" + "=" * 60)
    print("📏 文本相似度计算演示")
    print("=" * 60)
    
    demo = VectorDBDemo()
    
    # 计算两两之间的相似度
    texts = [
        "我喜欢编程",
        "我热爱写代码", 
        "今天天气不错",
        "今日晴朗无云"
    ]
    
    vectors = demo.text_to_vectors(texts)
    
    print("\n🔄 计算文本间的相似度:")
    print("-" * 40)
    
    # 计算余弦相似度
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            # 余弦相似度公式
            similarity = np.dot(vectors[i], vectors[j]) / \
                        (np.linalg.norm(vectors[i]) * np.linalg.norm(vectors[j]))
            
            print(f"'{texts[i]}' vs '{texts[j]}': {similarity:.3f}")

def demo_practical_application():
    """实际应用场景演示"""
    print("\n" + "=" * 60)
    print("💼 实际应用场景：简易问答系统")
    print("=" * 60)
    
    # 知识库
    knowledge_base = [
        "Python是一种高级编程语言，语法简洁易学",
        "Java是一种面向对象的编程语言，跨平台性强",
        "人工智能是计算机科学的一个重要分支",
        "机器学习是实现人工智能的一种方法",
        "深度学习是机器学习的一个子领域",
        "TensorFlow是一个流行的机器学习框架",
        "PyTorch是另一个优秀的深度学习框架"
    ]
    
    demo = VectorDBDemo()
    vectors = demo.text_to_vectors(knowledge_base)
    vector_db = demo.create_vector_db(vectors)
    
    # 问答系统
    def simple_qa_system(question):
        print(f"\n❓ 问题: {question}")
        indices, distances = demo.search_similar(vector_db, question, knowledge_base, k=1)
        answer = knowledge_base[indices[0]]
        print(f"💡 回答: {answer}")
        return answer
    
    # 测试问题
    questions = [
        "什么是Python？",
        "AI是什么意思？",
        "有哪些深度学习框架？"
    ]
    
    for question in questions:
        simple_qa_system(question)

def performance_comparison():
    """性能对比演示"""
    print("\n" + "=" * 60)
    print("⚡ 性能对比测试")
    print("=" * 60)
    
    import random
    import string
    
    # 生成测试数据
    def generate_random_text(length=10):
        return ''.join(random.choices(string.ascii_letters + ' ', k=length))
    
    # 不同规模的测试
    sizes = [100, 500, 1000]
    
    for size in sizes:
        print(f"\n📊 测试规模: {size} 条文本")
        texts = [generate_random_text() for _ in range(size)]
        
        demo = VectorDBDemo()
        
        # 计时
        start_time = time.time()
        vectors = demo.text_to_vectors(texts)
        encoding_time = time.time() - start_time
        
        start_time = time.time()
        vector_db = demo.create_vector_db(vectors)
        indexing_time = time.time() - start_time
        
        start_time = time.time()
        demo.search_similar(vector_db, "测试查询", texts, k=5)
        search_time = time.time() - start_time
        
        print(f"⏱️  编码时间: {encoding_time:.2f}秒")
        print(f"⏱️  索引时间: {indexing_time:.2f}秒") 
        print(f"⏱️  查询时间: {search_time:.4f}秒")

if __name__ == "__main__":
    print("🎓 欢迎学习向量数据库和嵌入模型！")
    print("这个演示将展示核心概念和实际应用")
    
    # 运行所有演示
    demo_basic_usage()
    demo_similarity_calculation() 
    demo_practical_application()
    performance_comparison()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！")
    print("现在你可以尝试修改代码来探索更多功能")
    print("=" * 60)