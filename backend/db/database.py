"""
SQLAlchemy 数据库模型定义
包含菜谱管理、聊天会话、聊天消息和文档块的数据表
"""
from langchain_core.documents import Document
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, 
    Enum, TIMESTAMP, JSON, ForeignKey, Index
)
from typing import List
from typing import Optional
from sqlalchemy.orm import declarative_base, relationship, sessionmaker,Mapped, mapped_column,Session
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Recipe(Base):
    """菜谱表"""
    __tablename__ = 'recipes'
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment='菜名')
    category:Mapped[str] = mapped_column(String(50), nullable=False, comment='分类')
    # 与文档处理器保持一致的中文难度枚举
    difficulty:Mapped[Optional[str]] = mapped_column(
        Enum('非常简单', '简单', '中等', '困难', '非常困难', '未知', name='difficulty_enum'),
        nullable=True,
        comment='难度'
    )
    content:Mapped[str] = mapped_column(Text, nullable=False, comment='完整的 Markdown 内容')
    file_path:Mapped[Optional[str]] = mapped_column(String(500), comment='原始文件路径')
    parent_id:Mapped[Optional[str]] = mapped_column(String(100), unique=True, comment='对应 document_processor 的 parent_id')
    
    # 关系
    chunks = relationship(
        "DocumentChunk",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_difficulty', 'difficulty'),
        Index('idx_parent_id', 'parent_id'),
    )
    
    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}', category='{self.category}')>"


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = 'chat_messages'
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id:Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='会话ID（格式：YYYYMMDD）'
    )
    message_id:Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='消息ID（同一session内的消息序号）'
    )
    role:Mapped[str] = mapped_column(
        Enum('user', 'assistant', 'system', name='role_enum'),
        comment='角色'
    )
    content:Mapped[str] = mapped_column(Text, nullable=False, comment='消息内容')
    intent:Mapped[Optional[str]] = mapped_column(String(50), comment='意图（list/detail/general）')
    rewrited_query:Mapped[Optional[str]] = mapped_column(Text, comment='重写后的查询')
    sources:Mapped[Optional[List[str]]] = mapped_column(JSON, comment='引用的菜谱来源')
    created_at:Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment='创建时间'
    )
    
    # 索引
    __table_args__ = (
        Index('idx_session', 'session_id'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id='{self.session_id}', message_id={self.message_id}, role='{self.role}')>"


class DocumentChunk(Base):
    """文档块表"""
    __tablename__ = 'document_chunks'
    
    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id:Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment='对应 document_processor 的 chunk_id')
    parent_id:Mapped[str] = mapped_column(
        String(100),
        ForeignKey('recipes.parent_id'),
        nullable=False,
        comment='所属父文档'
    )
    content:Mapped[str] = mapped_column(Text, nullable=False, comment='块内容')
    chunk_index:Mapped[int] = mapped_column(Integer, comment='在父文档中的序号')
    
    # 关系
    recipe = relationship("Recipe", back_populates="chunks")
    
    # 索引
    __table_args__ = (
        Index('idx_parent', 'parent_id'),
        Index('idx_chunk_id', 'chunk_id'),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, chunk_id='{self.chunk_id}', parent_id='{self.parent_id}')>"


# ==================== 数据库连接和会话管理 ====================

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        初始化数据库管理器
        
        Args:
            database_url: 数据库连接 URL
            echo: 是否打印 SQL 语句
        """
        self.engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,       # 避免 MySQL 连接空闲被断开
            pool_recycle=3600         # 定期回收连接
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_all_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        print("所有表创建成功！")
    
    def drop_all_tables(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(self.engine)
        print("所有表已删除！")
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def connect(self):
        try:
            with self.engine.connect() as conn:
                print("数据库连接成功！")
                return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    def disconnect(self):
        """断开数据库连接"""
        self.SessionLocal.close_all()
        self.engine.dispose()
        print("数据库连接已断开！")


    def save_document_to_db(self,doc:Document,session:Session)->None:
        """将文档保存到数据库"""
        try:
            # 规范化难度，确保在枚举集合内或为 None
            raw_difficulty = doc.metadata.get('difficulty')
            difficulty = raw_difficulty if raw_difficulty in {'非常简单','简单','中等','困难','非常困难','未知'} else None

            recipe = Recipe(
                name=doc.metadata.get('name','Unnamed Recipe'),
                category=doc.metadata.get('category','Uncategorized'),
                difficulty=difficulty,
                content=doc.page_content,
                file_path=doc.metadata.get('source',''),
                parent_id=doc.metadata.get('parent_id','')
            )
            session.add(recipe)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"保存文档到数据库失败: {e}")
        
    def save_chunk_to_db(self,chunk:Document,session:Session)->None:
        """将文档块保存到数据库"""
        try:
            chunk_obj = DocumentChunk(
                chunk_id=chunk.metadata.get('chunk_id',''),
                parent_id=chunk.metadata.get('parent_id',''),
                content=chunk.page_content,
                chunk_index=chunk.metadata.get('chunk_index',0)
            )
            session.add(chunk_obj)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"保存文档块到数据库失败: {e}")

    def select_parent_by_id(self,parent_id:str)->Optional[Recipe]:
        """通过parent_id查询菜谱"""
        try:
            session = self.get_session()
            recipe = session.query(Recipe).filter(Recipe.parent_id == parent_id).first()
            session.close()
            return recipe
        except Exception as e:
            print(f"查询菜谱失败: {e}")
            return None
        
    def select_recipes(self,page:int,page_size:int,category:Optional[str]=None,difficulty:Optional[str]=None):
        """查询菜谱列表，支持按分类和难度过滤，分页返回"""
        try:
            session = self.get_session()
            query = session.query(Recipe)
            if category:
                query = query.filter(Recipe.category == category)
            if difficulty:
                query = query.filter(Recipe.difficulty == difficulty)
            total = query.count()
            recipes = query.offset((page - 1) * page_size).limit(page_size).all()
            session.close()
            return total, recipes
        except Exception as e:
            print(f"查询菜谱列表失败: {e}")
            return 0, []
    
    def select_recipe_by_id(self,recipe_id:int)->Optional[Recipe]:
        """通过ID查询菜谱"""
        try:
            session = self.get_session()
            recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
            session.close()
            return recipe
        except Exception as e:
            print(f"查询菜谱失败: {e}")
            return None

    def get_chat_message(self,session_id:str,message_id:int)->ChatMessage:
        try:
            session = self.get_session()
            message = session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.message_id == message_id
            ).all()
            session.close()
            return message[0]
        except Exception as e:
            print(f"查询聊天消息失败: {e}")
            return None

    def get_chat_history(self,session_id:str)->List[ChatMessage]:
        try:
            session = self.get_session()
            messages = session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.message_id).all()
            session.close()
            return messages
        except Exception as e:
            print(f"查询聊天历史失败: {e}")
            return []

    def get_or_create_session_id(self, date: Optional[datetime] = None) -> str:
        """
        获取或创建当天的session_id
        
        Args:
            user_id: 用户ID
            date: 日期（默认为今天）
            
        Returns:
            session_id: 格式为 user_id_YYYYMMDD
        """
        if date is None:
            date = datetime.now()
        date_str = date.strftime('%Y%m%d')
        session_id = f"{date_str}"
        return session_id
    
    def get_next_message_id(self, session_id: str, session: Session) -> int:
        """
        获取指定session中的下一个message_id
        
        Args:
            session_id: 会话ID
            session: 数据库会话
            
        Returns:
            message_id: 下一个消息序号（从1开始）
        """
        try:
            # 查询当前session中最大的message_id
            max_id = session.query(func.max(ChatMessage.message_id)).filter(
                ChatMessage.session_id == session_id
            ).scalar()
            
            # 如果没有消息，返回1；否则返回最大值+1
            return 1 if max_id is None else max_id + 1
        except Exception as e:
            print(f"获取下一个message_id失败: {e}")
            return 1
    
    def get_session_messages(self, session_id: str, session: Session) -> List[ChatMessage]:
        """
        获取指定session的所有消息
        
        Args:
            session_id: 会话ID
            session: 数据库会话
            
        Returns:
            消息列表（按message_id排序）
        """
        try:
            messages = session.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.message_id).all()
            return messages
        except Exception as e:
            print(f"获取session消息失败: {e}")
            return []

    def save_chat_message(self,chat_message:ChatMessage,session:Session)->None:
        """将聊天消息保存到数据库"""
        try:
            session.add(chat_message)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"保存聊天消息到数据库失败: {e}")

    def delete_chat_history(self)->None:
        """删除所有聊天历史（谨慎使用）"""
        try:
            session = self.get_session()
            num_deleted = session.query(ChatMessage).delete()
            session.commit()
            session.close()
            print(f"已删除 {num_deleted} 条聊天历史记录！")
        except Exception as e:
            print(f"删除聊天历史失败: {e}")
    
    def get_history_lists(self)->List[str]:
        try:
            session = self.get_session()
            # 只取有消息的 session_id，并按 created_at 最大值倒序
            sub_last = (
                session.query(
                    ChatMessage.session_id,
                    func.max(ChatMessage.created_at).label("last_time")
                )
                .group_by(ChatMessage.session_id)
                .subquery()
            )

            rows = (
                session.query(sub_last.c.session_id)
                .order_by(sub_last.c.last_time.desc())
                .all()
            )
            session.close()

            return [r[0] for r in rows]
        except Exception as e:
            print(f"获取历史 session 列表失败: {e}")
            return []


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 数据库连接配置
    DATABASE_URL = "mysql+pymysql://cooker:Lu123456?@localhost:3306/recipt_db?charset=utf8mb4"
    
    # 创建数据库管理器
    db_manager = DatabaseManager(DATABASE_URL, echo=True)
    
    # 测试连接
    if db_manager.test_connection():
        # 创建所有表
        db_manager.create_all_tables()



