#检索优化模块
import logging
from typing import List, Dict, Any
import jieba
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder  
logger = logging.getLogger(__name__)

def chinese_tokenizer(text: str):
    """中文分词：使用 jieba，把字符串切成 token 列表"""
    # 去掉多余空白，再用 jieba.lcut 切词
    return [t.strip() for t in jieba.lcut(text) if t.strip()]


class RecipeRetrievalOptimizer:
    """菜谱检索优化器"""
    def __init__(self, vectorstore: FAISS, chunks: List[Document]):
        self.vectorstore = vectorstore
        self.chunks = chunks
        self.retriever = None
        self.setup_retriever()

        try:
            self.reranker = CrossEncoder("BAAI/bge-reranker-base")
            logger.info("重排模型 BAAI/bge-reranker-base 加载成功")
        except Exception as e:
            logger.error(f"重排模型加载失败: {e}")
            self.reranker = None


    def model_rerank(self, query: str, candidates: List[Document], k: int = 5) -> List[Document]:
        """
        使用重排模型对候选文档进行重排序

        Args:
            query: 用户查询
            candidates: 候选文档列表（来自向量检索 / 混合检索）
            k: 返回前 k 个结果

        Returns:
            重排后的文档列表
        """
        if not self.reranker:
            logger.warning("重排模型未初始化，直接返回原始候选")
            return candidates[:k]

        if not candidates:
            return []

        # CrossEncoder 输入为 [query, document] 对
        model_inputs = [[query, doc.page_content] for doc in candidates]

        # 得到每个候选的相关性分数（越大越相关）
        scores = self.reranker.predict(model_inputs)

        # 把分数附加到文档上，然后排序
        doc_with_scores = []
        for doc, score in zip(candidates, scores):
            # 把重排分数写到 metadata 里，方便调试
            doc.metadata["rerank_score"] = float(score)
            doc_with_scores.append((doc, score))

        # 按分数从高到低排序
        doc_with_scores.sort(key=lambda x: x[1], reverse=True)

        reranked_docs = [d for d, _ in doc_with_scores[:k]]

        logger.info(
            f"重排模型完成: 候选 {len(candidates)} 条, 返回前 {len(reranked_docs)} 条"
        )
        return reranked_docs

    def setup_retriever(self):
        """
        设置向量检索器和BM25检索器
        """
        logger.info("设置向量检索器和BM25检索器")
        # 向量检索器
        self.vector_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10}
        )

        # BM25检索器
        self.bm25_retriever = BM25Retriever.from_documents(
            self.chunks,
            k=5,
            preprocess_func = chinese_tokenizer
        )

    def hybrid_search(self, query: str, k: int = 5) -> List[Document]:
        """
        混合检索 - 结合向量检索和BM25检索，使用RRF重排

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索到的文档列表
        """
        vector_docs = self.vector_retriever.invoke(query)
        bm25_docs = self.bm25_retriever.invoke(query)
        reranked_docs = self.rrf_rerank(vector_docs, bm25_docs)
        return reranked_docs[:k]


    def rrf_rerank(self, vector_docs: List[Document], bm25_docs: List[Document], k: int = 60) -> List[Document]:
        """
        使用RRF (Reciprocal Rank Fusion) 算法重排文档

        Args:
            vector_docs: 向量检索结果
            bm25_docs: BM25检索结果
            k: RRF参数，用于平滑排名

        Returns:
            重排后的文档列表
        """
        doc_scores = {}
        doc_objects = {}

        # 计算向量检索结果的RRF分数
        for rank, doc in enumerate(vector_docs):
            # 使用文档内容的哈希作为唯一标识
            doc_id = hash(doc.page_content)
            doc_objects[doc_id] = doc

            # RRF公式: 1 / (k + rank)
            rrf_score = 1.0 / (k + rank + 1)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

            logger.debug(f"向量检索 - 文档{rank+1}: RRF分数 = {rrf_score:.4f}")

        # 计算BM25检索结果的RRF分数
        for rank, doc in enumerate(bm25_docs):
            doc_id = hash(doc.page_content)
            doc_objects[doc_id] = doc

            rrf_score = 1.0 / (k + rank + 1)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

            logger.debug(f"BM25检索 - 文档{rank+1}: RRF分数 = {rrf_score:.4f}")

        # 按最终RRF分数排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # 构建最终结果
        reranked_docs = []
        for doc_id, final_score in sorted_docs:
            if doc_id in doc_objects:
                doc = doc_objects[doc_id]
                # 将RRF分数添加到文档元数据中
                doc.metadata['rrf_score'] = final_score
                reranked_docs.append(doc)
                logger.debug(f"最终排序 - 文档: {doc.page_content[:50]}... 最终RRF分数: {final_score:.4f}")

        logger.info(f"RRF重排完成: 向量检索{len(vector_docs)}个文档, BM25检索{len(bm25_docs)}个文档, 合并后{len(reranked_docs)}个文档")

        return reranked_docs

    def metadata_filtered_search(self, query: str, filters:Dict[str, Any], k: int = 10) -> List[Document]:
        """
        带元数据过滤的检索
        
        Args:
            query: 查询文本
            filters: 元数据过滤条件
            top_k: 返回结果数量
            
        Returns:
            过滤后的文档列表
        """
        # 先进行混合检索，获取更多候选
        docs = self.hybrid_search(query, k)

        filtered_docs = []
        for doc in docs:
            match = True
            for key, value in filters.items():
                if key in doc.metadata:
                    if isinstance(value, list):
                        if doc.metadata[key] not in value:
                            match = False
                            break
                    else:
                        if doc.metadata[key] != value:
                            match = False
                            break
                else:
                    match = False
                    break
            if match:
                filtered_docs.append(doc)
                if len(filtered_docs) >= k:
                    break
        return filtered_docs






