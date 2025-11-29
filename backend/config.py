"""
配置管理模块
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 获取当前文件所在目录
BASE_DIR = Path(__file__).resolve().parent

# 加载环境变量，指定 .env 文件路径
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """应用配置"""
    # Log配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")

    # 数据目录
    DATA_PATH: str = os.getenv("DATA_PATH", "data")
    DOCUMENT_PATH: str = os.getenv("DOCUMENT_PATH", "documents")
    CHUNKS_PATH: str = os.getenv("CHUNKS_PATH", "chunks")
    PARENT_CHILD_MAP_PATH: str = os.getenv("PARENT_CHILD_MAP_PATH", "parent_child_map")
    INDEX_PATH: str = os.getenv("INDEX_PATH", "index")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "NONE")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "NONE")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "NONE")
    DB_URL: str = os.getenv("DB_URL", "None")
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()

