from .llm_generation import RecipeLLMGeneration
from .rag_engine import RecipeRAGEngine
from ..config import Settings
import logging
from typing import List, Dict, Any
from ..db.database import DatabaseManager

logger = logging.getLogger(__name__)
class RecipeAgentService:
    """菜谱Agent服务 - 整合RAG引擎和LLM生成器的编排层"""
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化服务，注入RAG引擎和LLM生成器"""
        settings = Settings()
        self.rag_engine = RecipeRAGEngine(data_path=settings.DATA_PATH, 
                        document_path=settings.DOCUMENT_PATH, 
                        chunks_path=settings.CHUNKS_PATH, 
                        parent_child_map_path=settings.PARENT_CHILD_MAP_PATH, 
                        index_path=settings.INDEX_PATH, 
                        embedding_model_name=settings.EMBEDDING_MODEL_NAME,
                        db_manager=db_manager
                        )
        self.rag_engine.setup_rag_service()
        self.llm_generator = RecipeLLMGeneration(model_name=settings.MODEL_NAME)
        logger.info("菜谱Agent服务初始化完成")

    def query(self, user_query: str, filters: Dict[str, Any] = None, streaming: bool = False) -> Dict[str, Any]:
        """
        处理用户查询的主要入口
        """
        #1. 查询意图识别（调用 llm_generator.query_router）
        #2. 查询优化（调用 llm_generator.rewrite_query）
        rewrited_query = self.llm_generator.rewrite_query(user_query)['messages'][-1].content
        logger.info(f"重写后的查询: {rewrited_query}")
        router_result = self.llm_generator.query_router(rewrited_query)['messages'][-1].content.strip()
        logger.info(f"路由结果: {router_result}")

        #3. 检索相关文档（调用 rag_engine.retrieval_optimizer）
        if filters:
            logger.info(f"应用过滤器: {filters}")
            context_docs = self.rag_engine.retrieval_optimizer.metadata_filtered_search(rewrited_query,filters)
        else:
            context_docs = self.rag_engine.retrieval_optimizer.hybrid_search(rewrited_query, k=6)
        logger.info(f"检索到的上下文文档数量: {len(context_docs)}")

        #4. 回溯父文档（调用 document_processor.get_parent_document）
        parent_recipes = self.rag_engine.document_processor.get_parent_recipes(context_docs)
        logger.info(f"回溯到的父菜谱数量: {len(parent_recipes)}")

        #5. 构建上下文（调用 llm_generator.build_context）
        context = self.llm_generator.build_context(parent_recipes,3000)
        logger.info(f"构建的上下文长度: {len(context)}")
        #6. 生成答案（根据意图调用不同的生成方法）
        if router_result == "list":
            result_answer = self.llm_generator.list_question(rewrited_query, parent_recipes)
        elif router_result == "detail":
            result_answer = self.llm_generator.detail_question(rewrited_query, context,streaming=streaming)
        else:
            result_answer = self.llm_generator.general_question(rewrited_query, context,streaming=streaming)

        #7. 返回结果
        return {
                "rewrited_query": rewrited_query, 
                "intent": router_result, 
                "answer": result_answer,
                "parent_recipes": parent_recipes
                }
    
