#文档处理模块
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import pickle
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from ..db.database import DatabaseManager,Recipe
import uuid


logger = logging.getLogger(__name__)
class RecipeDocumentProcessor:
    """菜谱文档处理器"""
    CATEGORY_MAPPING = {
        'meat_dish': '荤菜',
        'vegetable_dish': '素菜',
        'soup': '汤品',
        'dessert': '甜品',
        'breakfast': '早餐',
        'staple': '主食',
        'aquatic': '水产',
        'condiment': '调料',
        'drink': '饮品'
    }
    CATEGORY_LABELS = list(set(CATEGORY_MAPPING.values()))
    DIFFICULTY_LABELS = ['非常简单', '简单', '中等', '困难', '非常困难']

    @classmethod
    def get_difficulty_label(cls) -> str:
        return cls.DIFFICULTY_LABELS
    
    @classmethod
    def get_category_label(cls) -> str:
        return cls.CATEGORY_MAPPING


    def __init__(self,data_path:str,document_path:str,chunks_path:str,parent_child_map_path:str,db_manager:DatabaseManager):
        """
        初始化菜谱文档处理器
        """
        self.parent_child_map_path = parent_child_map_path
        self.document_path = document_path
        self.chunks_path = chunks_path
        self.data_path = data_path
        # self.documents: List[Document] = [] #父文档(完整食谱)
        self.chunks: List[Document] = [] #子文档(按标题切割的小块)
        self.parent_child_map:Dict[str,str] = {}  # 子块ID -> 父文档ID的映射 
        self.db_manager = db_manager

    def load_documents(self) -> List[Document]:
        """加载所有菜谱"""
        logger.info(f"正在从{self.data_path}加载菜谱")
        if Path(self.document_path).exists():
            with open(self.document_path, "rb") as f:
                documents = pickle.load(f,encoding="utf-8")
            self.documents = documents
            logger.info(f"菜谱加载完成,加载路径: {self.document_path}")
            return documents
        documents = []
        data_path = Path(self.data_path)
        if not data_path.exists():
            logger.error(f"菜谱数据目录不存在: {self.data_path}")
            return []
        for md_file in data_path.rglob("*.md"):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                # 为每个父文档分配确定性的唯一ID（基于数据根目录的相对路径）
                try:
                    data_root = Path(self.data_path).resolve()
                    relative_path = Path(md_file).relative_to(data_root).as_posix()
                except Exception as e:
                    relative_path = Path(md_file).as_posix()
                parent_id = hashlib.md5(relative_path.encode("utf-8")).hexdigest()
                #创建Document对象
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(md_file),
                        "parent_id": parent_id,
                        "doc_type": "parent"
                    }
                )
                documents.append(doc)
            except Exception as e:
                logger.error(f"加载菜谱失败: {md_file} - {e}")
        #增强文档元数据
        session = self.db_manager.get_session()
        for doc in documents:
            self.enhance_metadata(doc)
            self.db_manager.save_document_to_db(doc, session)
        session.close()

        self.documents = documents
        with open(self.document_path, "wb") as f:
            pickle.dump(documents, f)
        logger.info(f"菜谱加载完成,保存路径: {self.document_path}")
        return documents

    def enhance_metadata(self, doc: Document) -> None:
        file_path = Path(doc.metadata.get("source"))
        path_parts = file_path.parts
        
        #提取菜品分类
        doc.metadata["category"] = "其他"
        for key, value in self.CATEGORY_MAPPING.items():
            if key in path_parts:
                doc.metadata["category"] = value
                break
        #提取菜品名称
        doc.metadata["name"] = file_path.stem
        #提取菜品难度
        content = doc.page_content
        if "预估烹饪难度：★★★★★" in doc.page_content:
            doc.metadata["difficulty"] = "非常困难"
        elif "预估烹饪难度：★★★★" in doc.page_content:
            doc.metadata["difficulty"] = "困难"
        elif "预估烹饪难度：★★★" in doc.page_content:
            doc.metadata["difficulty"] = "中等"
        elif "预估烹饪难度：★★" in doc.page_content:
            doc.metadata["difficulty"] = "简单"
        elif "预估烹饪难度：★" in doc.page_content:
            doc.metadata["difficulty"] = "非常简单"
        else:
            doc.metadata["difficulty"] = "未知"


    def markdown_header_spliter(self) -> List[Document]:
        """ 使用Markdown标题分割器进行结构化分割
            Returns:
            按标题结构分割的文档列表
            """
        if Path(self.chunks_path).exists():
            with open(self.chunks_path, "rb") as f:
                chunks = pickle.load(f,encoding="utf-8")
            self.chunks = chunks
            logger.info(f"子块加载完成,加载路径: {self.chunks_path}")
            # if Path(self.parent_child_map_path).exists():
            #     with open(self.parent_child_map_path, "rb") as f:
            #         self.parent_child_map = pickle.load(f)
            #     logger.info(f"父子映射加载完成,加载路径: {self.parent_child_map_path}")
            return chunks
        headers_to_split_on = [
            ("#","主标题"),
            ("##","二级标题"),
            ("###","三级标题"),
        ]
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on = headers_to_split_on,
            strip_headers = False
        )
        all_chunks = []
        session = self.db_manager.get_session()
        for doc in self.documents:
            try:
                content_preview = doc.page_content[:200]
                has_headers = any( line.strip().startswith("#") for line in content_preview.split("\n"))

                if not has_headers:
                    logger.warning(f"文档没有标题: {doc.metadata['source']}")
                    logger.debug(f"文档内容: {doc.page_content[:200]}")                
                
                md_chunks = splitter.split_text(doc.page_content)
                logger.debug(f"{doc.metadata['source']}分割后的切片数量: {len(md_chunks)}")

                if len(md_chunks) <= 1:
                    logger.warning(f"文档未能按照标题分割: {doc.metadata['source']}")

                parent_id = doc.metadata["parent_id"]
                for i, chunk in enumerate(md_chunks):
                    child_id = str(uuid.uuid4())
                    chunk.metadata.update(doc.metadata)
                    chunk.metadata.update(
                        {
                            "chunk_id": child_id,
                            "parent_id": parent_id,
                            "doc_type": "child",
                            "chunk_index": i,
                        }
                    )
                    all_chunks.append(chunk)
                    self.db_manager.save_chunk_to_db(chunk, session)
                    self.parent_child_map[child_id] = parent_id
                # with open(self.parent_child_map_path, "wb") as f:
                #     pickle.dump(self.parent_child_map, f)
                # logger.info(f"父子映射保存完成,保存路径: {self.parent_child_map_path}")
            except Exception as e:
                logger.error(f"Markdown标题分割失败: {doc.metadata['source']} - {e}")
                logger.exception(e)
                all_chunks.append(doc)
        logger.info(f"Markdown标题分割完成,生成{len(all_chunks)}个切片")
        session.close()
        with open(self.chunks_path, "wb") as f:
            pickle.dump(all_chunks, f)
        logger.info(f"子块保存完成,保存路径: {self.chunks_path}")
        self.chunks = all_chunks
        return all_chunks

    def filter_documents_by_category(self, category: str) -> List[Document]:
        """ 根据菜品分类过滤文档
        Args:
            category: 菜品分类
        Returns:
            符合分类的文档列表
        """
        return [doc for doc in self.documents if doc.metadata["category"] == category]
        
    def filter_documents_by_difficulty(self, difficulty: str) -> List[Document]:
        """ 根据菜品难度过滤文档
        Args:
            difficulty: 菜品难度
        Returns:
            符合难度的文档列表
        """
        return [doc for doc in self.documents if doc.metadata["difficulty"] == difficulty]

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据统计信息

        Returns:
            统计信息字典
        """
        if not self.documents:
            return {}
        
        categories = {}
        difficulties = {}

        for doc in self.documents:
            category = doc.metadata.get("category", "未知")
            difficulty = doc.metadata.get("difficulty", "未知")
            categories[category] = categories.get(category, 0) + 1
            difficulties[difficulty] = difficulties.get(difficulty, 0) + 1

        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "categories": categories,
            "difficulties": difficulties,
            "avg_chunk_size": sum(len(chunk.page_content) for chunk in self.chunks) / len(self.chunks) if self.chunks else 0
        }   


    def export_metadata(self, output_path: str) -> None:
        """
        将元数据导出为JSON文件
        Args:
            output_path: 输出路径
        """
        import json
        metadata_list = []
        for doc in self.documents:
            metadata_list.append(
                {
                    'source': doc.metadata.get("source", "未知"),
                    'name': doc.metadata.get("name", "未知"),
                    'category': doc.metadata.get("category", "未知"),
                    'difficulty': doc.metadata.get("difficulty", "未知"),
                    'content_length': len(doc.page_content)
                }
            )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)
        logger.info(f"元数据导出完成,导出路径: {output_path}")

    def get_parent_recipes(self, child_chunks: List[Document]) -> List[Recipe]:
        """
        根据子文档列表获取父文档列表
        Args:
            child_chunks: 子文档列表
        Returns:
            父文档
        """
        parent_relevance = {}
        parent_docs_map = {}

        for chunk in child_chunks:
            parent_id = chunk.metadata.get("parent_id", "未知")
            if parent_id:
                parent_relevance[parent_id] = parent_relevance.get(parent_id, 0) + 1

                # if parent_id not in parent_docs_map:
                #     for doc in self.documents:
                #         if doc.metadata.get("parent_id") == parent_id:
                #             parent_docs_map[parent_id] = doc    
                #             break
                if parent_id not in parent_docs_map:
                    try:
                        recipe = self.db_manager.select_parent_by_id(parent_id)
                        if recipe:
                            parent_docs_map[parent_id] = recipe
                    except Exception as e:
                        logger.error(f"查询父文档失败: {e}")
                        continue
        
        sorted_parent_ids = sorted(parent_relevance.keys(), key=lambda x: parent_relevance[x], reverse=True)

        parent_recipes = []
        for parent_id in sorted_parent_ids:
            if parent_id in parent_docs_map:
                parent_recipes.append(parent_docs_map[parent_id])
        
        parent_info = []
        for recipe in parent_recipes:
            name = recipe.name
            parent_id = recipe.parent_id
            relevance_count = parent_relevance.get(parent_id, 0)
            parent_info.append(f"父文档: {name} (ID: {parent_id}, 相关度: {relevance_count})")

        logger.info(f"从 {len(child_chunks)} 个子块中找到 {len(parent_recipes)} 个去重父文档: {', '.join(parent_info)}")
        return parent_recipes

# if __name__ == "__main__":
#     processor = RecipeDocumentProcessor(data_path="E:/algorithm_study/agent_learning/CookRag/dishes/meat_dish/宫保鸡丁")
#     documents = processor.load_documents()

