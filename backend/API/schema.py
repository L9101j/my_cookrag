from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QueryIntent(str, Enum):
    """查询意图"""
    LIST = "list"      # 列表推荐
    DETAIL = "detail"  # 详细制作
    GENERAL = "general"  # 通用问题


class Difficulty(str, Enum):
    """难度等级"""
    VERY_EASY = "非常简单"
    EASY = "简单"
    MEDIUM = "中等"
    HARD = "困难"
    VERY_HARD = "非常困难"
    UNKNOWN = "未知"


# ==================== 通用响应模型 ====================

class ApiResponse(BaseModel):
    """统一API响应格式"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    error: Optional[Dict[str, str]] = Field(None, description="错误详情")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="时间戳")


# ==================== 聊天相关 ====================

class ChatMessageRequest(BaseModel):
    """聊天消息请求"""
    message: str = Field(..., description="用户消息内容", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(default=None, description="可选的过滤器")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "宫保鸡丁怎么做？",
                "filters": {
                    "category": "meat_dish",
                    "difficulty": "简单"
                }
            }
        }



class ChatHistoryMessage(BaseModel):
    """历史消息"""
    message_id: int = Field(..., description="消息ID")
    role: MessageRole = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    intent: Optional[QueryIntent] = Field(None, description="查询意图（仅assistant）")
    sources: Optional[List[str]] = Field(None, description="来源（仅assistant）")
    timestamp: datetime = Field(..., description="时间戳")


class ChatHistoryResponse(BaseModel):
    """聊天历史响应"""
    session_id: str = Field(..., description="会话ID")
    total: int = Field(..., description="消息总数")
    messages: List[ChatHistoryMessage] = Field(..., description="消息列表")


# ==================== 菜谱相关 ====================

class RecipeListQuery(BaseModel):
    """菜谱列表查询参数"""
    category: Optional[str] = Field(None, description="分类")
    difficulty: Optional[Difficulty] = Field(None, description="难度")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class RecipePreview(BaseModel):
    """菜谱预览"""
    id: int = Field(..., description="菜谱ID")
    name: str = Field(..., description="菜名")
    category: str = Field(..., description="分类")
    difficulty: Optional[Difficulty] = Field(None, description="难度")
    preview: Optional[str] = Field(None, description="内容预览")


class RecipeListResponse(BaseModel):
    """菜谱列表响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    recipes: List[RecipePreview] = Field(..., description="菜谱列表")


class RecipeDetail(BaseModel):
    """菜谱详情"""
    id: int = Field(..., description="菜谱ID")
    name: str = Field(..., description="菜名")
    category: str = Field(..., description="分类")
    difficulty: Optional[Difficulty] = Field(None, description="难度")
    content: str = Field(..., description="完整内容（Markdown）")


