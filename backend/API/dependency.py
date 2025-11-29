import datetime
from .schema import ApiResponse
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from ..modules.agent_service import RecipeAgentService
from ..db.database import DatabaseManager,ChatMessage


# ==================== 工具函数 ====================

def create_api_response(data: any = None, message: str = "success", code: int = 200):
    """创建统一的 API 响应"""
    return ApiResponse(code=code, message=message, data=data)


def create_error_response(message: str, code: int = 400, error_type: str = "Error", details: str = ""):
    """创建错误响应"""
    return ApiResponse(
        code=code,
        message=message,
        error={"type": error_type, "details": details}
    )

def process_agent_response(agent_response: dict, user_query: str, session_id: str, message_id: int) -> dict:
    rewrited_query = agent_response["rewrited_query"]
    intent = agent_response["intent"]
    yield_answer = agent_response["answer"]
    parent_recipes = agent_response["parent_recipes"]
    recipes =[recipe.name for recipe in parent_recipes]
    response = ChatMessage(
        message_id=message_id,
        session_id=session_id,
        intent=intent,
        role = 'user',
        content = user_query,
        rewrited_query=rewrited_query,
        sources=[],
        created_at=datetime.datetime.now()
    )
    return yield_answer,response,recipes



# ==================== 依赖注入函数 ====================

def get_db_manager() -> DatabaseManager:
    """
    获取数据库管理器的依赖注入函数
    
    Returns:
        DatabaseManager: 数据库管理器实例
        
    Raises:
        HTTPException: 当数据库服务未初始化时抛出 503 错误
    """
    from .main import db_manager
    if db_manager is None:
        raise HTTPException(
            status_code=503, 
            detail="数据库服务未就绪，请稍后重试"
        )
    return db_manager


def get_agent_service() -> RecipeAgentService:
    """
    获取 Agent 服务的依赖注入函数
    
    Returns:
        RecipeAgentService: Agent 服务实例
        
    Raises:
        HTTPException: 当 Agent 服务未初始化时抛出 503 错误
    """
    from .main import agent_service
    if agent_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Agent 服务未就绪，请稍后重试"
        )
    return agent_service


