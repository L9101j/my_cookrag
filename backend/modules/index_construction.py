#索引构建
import logging
from typing import List
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class RecipeIndexBuilder:
    """菜谱索引构建器"""
    def __init__(self, embedding_model_name: str, index_path: str):
        """初始化菜谱索引构建器"""
        self.embedding_model_name = embedding_model_name
        self.index_path = index_path
        self.embeddings = None
        self.vectorstore = None
        self.setup_embeddings()
    
    def setup_embeddings(self):
        """设置嵌入模型"""
        logger.info(f"设置嵌入模型: {self.embedding_model_name}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={"device": "cuda"},
            encode_kwargs={"normalize_embeddings": True}
        )
        logger.info(f"嵌入模型设置完成")

    def build_index(self, chunks: List[Document]) -> FAISS:
        """构建FAISS索引"""
        logger.info(f"构建FAISS索引")
        if not chunks:
            raise ValueError("没有可构建索引的子块")
        self.vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )   

        logger.info(f"FAISS索引构建完成,包含{len(chunks)}个子块")
        return self.vectorstore
    
    def add_new_chunks(self, new_chunks: List[Document]) -> None:
        """添加新的子块到索引"""
        logger.info(f"添加{len(new_chunks)}个子块到索引")
        if not new_chunks:
            raise ValueError("没有可添加的子块")
        self.vectorstore.add_documents(new_chunks)
        logger.info(f"子块添加完成")

    def save_index(self) -> None:
        """保存FAISS索引"""
        logger.info(f"保存FAISS索引到: {self.index_path}")
        if not self.vectorstore:
            raise ValueError("没有可保存的索引")
        Path(self.index_path).mkdir(parents=True, exist_ok=True)
        self.vectorstore.save_local(self.index_path)
        logger.info(f"FAISS索引保存完成,保存路径: {self.index_path}")
    
    def load_index(self) -> bool:
        """加载FAISS索引"""
        logger.info(f"加载FAISS索引从: {self.index_path}")
        if not self.embeddings:
            self.setup_embeddings()
        
        if not Path(self.index_path).exists():
            logger.error(f"FAISS索引文件不存在: {self.index_path}")
            return False
        self.vectorstore = FAISS.load_local(self.index_path, self.embeddings,allow_dangerous_deserialization=True)
        logger.info(f"FAISS索引加载完成,加载路径: {self.index_path}")
        return True
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """相似度搜索"""
        logger.info(f"相似度搜索: {query}, 返回{k}个相似文档")
        if not self.vectorstore:
            raise ValueError("没有可搜索的索引")
        return self.vectorstore.similarity_search(query, k)

