#fastapi主程序
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
import uuid
import logging
from typing import Optional
from ..logging_config import setup_logging
from ..config import Settings
from ..modules.agent_service import RecipeAgentService
from ..db.database import DatabaseManager

setup_logging()
logger = logging.getLogger(__name__)

agent_service: Optional[RecipeAgentService] = None
db_manager: Optional[DatabaseManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global agent_service, db_manager
    try:
        # 应用启动时初始化服务和数据库连接
        logger.info("正在初始化应用...")
        settings = Settings()
        # 初始化数据库管理器（同步操作）
        db_manager = DatabaseManager(database_url=settings.DB_URL)
        # 启动时探活数据库连接，便于尽早发现配置或服务问题
        logger.info("数据库管理器初始化成功")
        
        # 初始化Agent服务
        agent_service = RecipeAgentService(db_manager=db_manager)
        logger.info("Agent服务初始化成功")
        
        logger.info("应用启动完成")
        yield
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        raise
    finally:
        # 应用关闭时清理资源
        logger.info("正在关闭应用...")
        agent_service = None
        db_manager.disconnect()
        db_manager = None
        logger.info("应用关闭完成")

# 创建 FastAPI 应用
app = FastAPI(
    title="CookRag API",
    description="智能菜谱问答系统 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost"],  # Vue/React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延迟导入路由以避免循环导入
from .routes import chat, surf
app.include_router(chat.router, prefix="/api")
app.include_router(surf.router, prefix="/api")



# ==================== 健康检查 ====================

@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {"message": "CookRag API is running", "version": "1.0.0"}


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "agent_service": agent_service is not None,
        "db_manager": db_manager is not None
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



