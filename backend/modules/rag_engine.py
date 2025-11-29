#RAG引擎模块
import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from .index_construction import RecipeIndexBuilder
from .retrieval_optimization import RecipeRetrievalOptimizer
from .document_processor import RecipeDocumentProcessor
from ..config import Settings
from ..db.database import DatabaseManager

logger = logging.getLogger(__name__)
class RecipeRAGEngine:
    """菜谱RAG引擎"""
    def __init__(self, data_path:str, document_path:str, chunks_path:str, parent_child_map_path:str, index_path:str, embedding_model_name:str, db_manager:DatabaseManager):
        """初始化菜谱RAG引擎"""
        self.data_path = data_path
        self.document_path = document_path
        self.chunks_path = chunks_path
        self.parent_child_map_path = parent_child_map_path
        self.index_path = index_path
        self.embedding_model_name = embedding_model_name
        self.document_processor = None
        self.index_builder = None
        self.retrieval_optimizer = None
        self.db_manager = db_manager
        
    def setup_rag_service(self) -> None:
        """设置RAG服务"""
        logger.info("设置RAG服务")
        self.document_processor = RecipeDocumentProcessor(
            data_path=self.data_path,
            document_path=self.document_path,
            chunks_path=self.chunks_path,
            parent_child_map_path=self.parent_child_map_path,
            db_manager=self.db_manager
        )
        
        #获取所有菜谱文档
        documents = self.document_processor.load_documents()
        #获取所有子块
        chunks = self.document_processor.markdown_header_spliter()
        #获取数据统计信息
        statistics = self.document_processor.get_statistics()
        logger.info(f"数据统计信息: {statistics}")
        #将元数据导出为JSON文件
        self.document_processor.export_metadata(output_path="E:/algorithm_study/agent_learning/CookRag/backend/temp/metadata.json")
        #加载FAISS索引
        self.index_builder = RecipeIndexBuilder(embedding_model_name=self.embedding_model_name, index_path=self.index_path)
        if self.index_builder.load_index():
            logger.info("FAISS索引加载完成")
        else:
            #构建FAISS索引
            self.index_builder.build_index(chunks)
            #保存FAISS索引
            self.index_builder.save_index()
        vectorstore = self.index_builder.vectorstore
        self.retrieval_optimizer = RecipeRetrievalOptimizer(vectorstore, chunks)
        logger.info("RAG服务设置完成")

if __name__ == "__main__":
    from ..logging_config import setup_logging

    setup_logging()
    settings = Settings()
    rag_engine = RecipeRAGEngine(data_path=settings.DATA_PATH, 
                        document_path=settings.DOCUMENT_PATH, 
                        chunks_path=settings.CHUNKS_PATH, 
                        parent_child_map_path=settings.PARENT_CHILD_MAP_PATH, 
                        index_path=settings.INDEX_PATH, 
                        embedding_model_name=settings.EMBEDDING_MODEL_NAME,
                        db_url=settings.DB_URL
                        )
    rag_engine.setup_rag_service()
    print(rag_engine.retrieval_optimizer.hybrid_search("宫保鸡丁"))
    # print(rag_engine.retrieval_optimizer.metadata_filtered_search("宫保鸡丁", filters={"category": "荤菜"}))
    print(rag_engine.document_processor.get_parent_recipes(rag_engine.retrieval_optimizer.hybrid_search("宫保鸡丁")))
