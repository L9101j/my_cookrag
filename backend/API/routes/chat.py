from fastapi import APIRouter, HTTPException, Depends
from ..schema import (
    ApiResponse,
    ChatMessageRequest,
    ChatHistoryMessage
)
from ..dependency import get_db_manager, get_agent_service, create_api_response, create_error_response,process_agent_response
from ...db.database import ChatMessage
from ...modules.agent_service import RecipeAgentService
from ...db.database import DatabaseManager
import json 
import logging
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk
from typing import Iterator
import datetime

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天对话API"])


@router.post("/query_response",  description="处理用户的聊天查询请求")
async def chat_query(
    request: ChatMessageRequest, 
    db_manager: DatabaseManager = Depends(get_db_manager), 
    agent_service: RecipeAgentService = Depends(get_agent_service)
):
    session_id = db_manager.get_or_create_session_id()
    db_session = db_manager.get_session()
    message_id = db_manager.get_next_message_id(session_id, db_session)
    user_query, user_filters = request.message, request.filters
    
    try:
        agent_response = agent_service.query(user_query, user_filters, streaming=True)
        yield_answer, user_chatmessage,recipes = process_agent_response(agent_response, user_query, session_id, message_id)
        # 先保存用户消息
        db_manager.save_chat_message(user_chatmessage, db_session)
        # 包装生成器：边流式输出边收集完整内容
        full_content = []
        
        def stream_and_collect():
            try:
                for chunk in yield_answer:
                    full_content.append(chunk)
                    yield chunk
            finally:
                # 流式输出结束后保存 AI 回复
                ai_message = ChatMessage(
                    session_id=session_id,
                    message_id=message_id + 1,  # AI 消息 ID
                    intent = user_chatmessage.intent,
                    rewrited_query=user_chatmessage.rewrited_query,
                    sources=recipes,
                    role="assistant",
                    content="".join(full_content),
                    created_at=datetime.datetime.now()
                )
                db_manager.save_chat_message(ai_message, db_session)
                db_session.commit()
                logger.info(f"已保存 AI 回复到数据库，session={session_id}, message_id={message_id + 1}")
        
        return StreamingResponse(
            stream_and_collect(), 
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"处理查询失败: {e}", exc_info=True)
        return create_error_response(
            message=f"处理查询失败: {e}", 
            code=500, 
            error_type="AgentError", 
            details=str(e)
        )



@router.get("/get_id", response_model= ApiResponse,description="请求的同时获取该请求的session_id和message_id")
async def get_id(db_manager: DatabaseManager = Depends(get_db_manager)):
    try:
        session_id = db_manager.get_or_create_session_id()
        db_session = db_manager.get_session()
        message_id = db_manager.get_next_message_id(session_id, db_session)
        return create_api_response(
            message="成功获取 session_id 和 message_id",
            code=200,
            data={
                "session_id": session_id,
                "message_id": message_id
            }
        )
    except Exception as e:
        logger.error(f"获取 session_id 和 message_id 失败: {e}", exc_info=True)
        return create_error_response(
            message=f"获取 session_id 和 message_id 失败: {e}",
            code=500,
            error_type="DatabaseError",
            details=str(e)
        )

def get_sources_from_db(
    session_id: str,
    message_id: int,
    db_manager: DatabaseManager
):
    """根据 session_id 和 message_id 获取菜谱名称列表"""
    chat_message = db_manager.get_chat_message(session_id, message_id)
    if chat_message and chat_message.sources:
        return chat_message.sources
    return []

@router.get("/get_sources", response_model= ApiResponse,description="根据session_id和message_id获取菜谱名称列表")
async def get_sources(
    session_id: str,
    message_id: int,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    try:
        sources = get_sources_from_db(session_id, message_id, db_manager)
        return create_api_response(
            message="成功获取菜谱名称列表",
            code=200,
            data={
                "sources": sources
            }
        )
    except Exception as e:
        logger.error(f"获取菜谱名称列表失败: {e}", exc_info=True)
        return create_error_response(
            message=f"获取菜谱名称列表失败: {e}",
            code=500,
            error_type="DatabaseError",
            details=str(e)
        )

@router.get("/history/{session_id}", response_model= ApiResponse,description="获取指定会话的聊天历史记录")
async def get_chat_history(
    session_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    try:
        history_messages = db_manager.get_chat_history(session_id)
        history_data = [
            ChatHistoryMessage(
                message_id=msg.message_id,
                role=msg.role,
                content=msg.content,
                intent=msg.intent,
                sources=msg.sources,
                timestamp=msg.created_at
            ) for msg in history_messages
        ]
        return create_api_response(
            message="成功获取聊天历史记录",
            code=200,
            data={
                "session_id": session_id,
                "history": history_data
            }
        )
    except Exception as e:
        logger.error(f"获取聊天历史记录失败: {e}", exc_info=True)
        return create_error_response(
            message=f"获取聊天历史记录失败: {e}",
            code=500,
            error_type="DatabaseError",
            details=str(e)
        )

@router.delete("/clear_history", response_model= ApiResponse,description="清除所有的聊天历史记录")
async def clear_chat_history(
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    try:
        db_manager.delete_chat_history()
        return create_api_response(
            message="成功清除所有聊天历史记录",
            code=200,
        )
    except Exception as e:
        logger.error(f"清除聊天历史记录失败: {e}", exc_info=True)
        return create_error_response(
            message=f"清除聊天历史记录失败: {e}",
            code=500,
            error_type="DatabaseError",
            details=str(e)
        )

@router.get("/history_lists", response_model=ApiResponse, description="获取所有有聊天记录的日期列表")
async def get_history_lists(
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    try:
        session_ids = db_manager.get_history_lists()
        items = [sid for sid in session_ids]
        return create_api_response(
            message="成功获取历史会话日期列表",
            code=200,
            data={"sessions": items}
        )
    except Exception as e:
        logger.error(f"获取历史会话日期列表失败: {e}", exc_info=True)
        return create_error_response(
            message=f"获取历史会话日期列表失败: {e}",
            code=500,
            error_type="DatabaseError",
            details=str(e)
        )


