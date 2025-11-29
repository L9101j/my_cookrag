#LLM生成模块构建
import logging
from typing import List, Dict, Any
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain_core.documents import Document
from langchain_core.messages import AIMessageChunk
from ..db.database import Recipe
import os
from ..config import settings

logger = logging.getLogger(__name__)
class RecipeLLMGeneration:
    """菜谱LLM生成器"""
    def __init__(self, model_name: str):
        self.model_name = "deepseek-chat" if model_name == "DEEPSEEK" else None
        self.model_provider = "deepseek" if model_name == "DEEPSEEK" else None
        self.llm = None
        self.setup_llm()

    def setup_llm(self):
        """设置LLM模型"""
        os.environ["DEEPSEEK_API_KEY"] = settings.DEEPSEEK_API_KEY
        self.llm = init_chat_model(
            model=self.model_name,
            model_provider=self.model_provider
        )

    def query_router(self, query: str):
        """查询路由"""
        classification_prompt = f"""
        你是一个菜谱问答分类器。请根据用户问题判断其意图，只能输出以下三个标签之一：
        - list：当用户想要获取菜品列表或推荐（只需要菜名），如“推荐几个素菜”“有什么川菜”“给我3个简单的菜”。
        - detail：当用户想要具体的制作方法、步骤或所需食材，如“宫保鸡丁怎么做”“需要哪些材料”“制作步骤是什么”。
        - general：其他泛化或背景类问题，如“什么是川菜”“烹饪技巧”“营养价值”。

        请注意：
        1. 只返回标签本身，不要多写任何文字。
        2. 如果问题同时包含多个意图，以用户最主要的需求判断。
        3. 若问题无法确定，返回 general。

        用户问题：{query}
        标签："""
        
        classification_chain = create_agent(
            model=self.llm,
            tools=[]
        )
        result = classification_chain.invoke({"messages": [{"role": "user", "content": classification_prompt}]})
        return result


    def general_question(self,query:str,context:str,streaming:bool=False):
        """通用问题"""
        general_prompt = f"""
            你是一位专业的烹饪助手。请根据以下食谱信息回答用户的问题。

            用户问题: {query}

            相关食谱信息:
            {context}

            请提供详细、实用的回答。如果信息不足，请诚实说明。

            回答:
            """
        
        general_chain = create_agent(
            model=self.llm,
            tools=[]
        )
        if streaming:
            for token, meta in general_chain.stream({"messages": [{"role": "user", "content": general_prompt}]},
                                              stream_mode="messages"
                                              ):
                if isinstance(token, AIMessageChunk):
                    yield token.content
        else:
            return general_chain.invoke({"messages": [{"role": "user", "content": general_prompt}]})
    
    
    def rewrite_query(self,query:str):
        prompt = f"""
        你是一个智能查询分析助手。请分析用户的查询，判断是否需要重写以提高食谱搜索效果。

        原始查询: {query}

        分析规则：
        1. **具体明确的查询**（直接返回原查询）：
        - 包含具体菜品名称：如"宫保鸡丁怎么做"、"红烧肉的制作方法"
        - 明确的制作询问：如"蛋炒饭需要什么食材"、"糖醋排骨的步骤"
        - 具体的烹饪技巧：如"如何炒菜不粘锅"、"怎样调制糖醋汁"

        2. **模糊不清的查询**（需要重写）：
        - 过于宽泛：如"做菜"、"有什么好吃的"、"推荐个菜"
        - 缺乏具体信息：如"川菜"、"素菜"、"简单的"
        - 口语化表达：如"想吃点什么"、"有饮品推荐吗"

        重写原则：
        - 保持原意不变
        - 增加相关烹饪术语
        - 优先推荐简单易做的
        - 保持简洁性

        示例：
        - "做菜" → "简单易做的家常菜谱"
        - "推荐个菜" → "简单家常菜推荐"
        - "川菜" → "经典川菜菜谱"
        - "宫保鸡丁怎么做" → "宫保鸡丁怎么做"（保持原查询）
        - "红烧肉需要什么食材" → "红烧肉需要什么食材"（保持原查询）

        请输出最终查询（如果不需要重写就返回原查询）:"""
        rewrite_chain = create_agent(
            model=self.llm,
            tools=[]
        )
        
        return rewrite_chain.invoke({"messages": [{"role": "user", "content": prompt}]})



    def detail_question(self,query:str,context:str,streaming:bool=False):
        """详细问题"""
        detail_prompt = f"""
            你是一位专业的烹饪导师。请根据食谱信息，为用户提供详细的分步骤指导。

            用户问题: {query}

            相关食谱信息:
            {context}

            请灵活组织回答，建议包含以下部分（可根据实际内容调整）：

            ## 🥘 菜品介绍
            [简要介绍菜品特点和难度]

            ## 🛒 所需食材
            [列出主要食材和用量]

            ## 👨‍🍳 制作步骤
            [详细的分步骤说明，每步包含具体操作和大概所需时间]

            ## 💡 制作技巧
            [仅在有实用技巧时包含。如果原文的"附加内容"与烹饪无关或为空，可以基于制作步骤总结关键要点，或者完全省略此部分]

            注意：
            - 根据实际内容灵活调整结构
            - 不要强行填充无关内容
            - 重点突出实用性和可操作性

            回答:
            """
        
        detail_chain = create_agent(
            model=self.llm,
            tools=[]
        )
        if streaming:
            for token, meta in detail_chain.stream({"messages": [{"role": "user", "content": detail_prompt}]},
                                             stream_mode="messages"
                                              ):
                if isinstance(token, AIMessageChunk):
                    yield token.content
        else:
            return detail_chain.invoke({"messages": [{"role": "user", "content": detail_prompt}]})


    def list_question(self,query:str,context_docs:List[Recipe]):
        if not context_docs:
            return "抱歉，没有找到相关食谱"
        dish_names = []
        for doc in context_docs:
            dish_name = doc.name if hasattr(doc, "name") else "未知"
            if dish_name not in dish_names:
                dish_names.append(dish_name)
        if len(dish_names) == 1:
            return f"为您推荐：{dish_names[0]}"
        else:
            return f"为您推荐以下菜品：\n" + "\n".join([f"{i+1}. {name}" for i, name in enumerate(dish_names)])
        

    def build_context(self,docs:List[Recipe],maxlength:int=2000)->str:
        """构建上下文"""
        if not docs:
            logger.warning("没有可构建上下文的文档")
            return ""
        context_parts = []
        context_length = 0
        for i, doc in enumerate(docs):
            # metadata = doc.metadata
            # metadata_info = f"食谱{i}:"
            # if "name" in metadata:
            #     metadata_info += f"菜名: {metadata['name']}\n"
            # if "category" in metadata:
            #     metadata_info += f"分类: {metadata['category']}\n"
            # if "difficulty" in metadata:
            #     metadata_info += f"难度: {metadata['difficulty']}\n"
            metadata_info = f"食谱{i}: 菜名: {doc.name}, 分类: {doc.category}, 难度: {doc.difficulty}\n"
            doc_text = f"metadata_info:{metadata_info}\n{doc.content}"
            if context_length + len(doc_text) <= maxlength:
                context_parts.append(doc_text)
                context_length += len(doc_text)
            else:
                break
        return "\n".join(context_parts)

if __name__ == "__main__":
    llm_generator = RecipeLLMGeneration(model_name="DEEPSEEK")
    query = "宫保鸡丁怎么做"
    context = "宫保鸡丁是一道中国传统的名菜，主要由鸡肉、姜、蒜、料酒、盐、味精、油组成。"
    rewrite_result = llm_generator.rewrite_query(query)
    print("重写结果:", rewrite_result)
    # 从 agent 响应中提取文本内容
    rewrite_query = rewrite_result['messages'][-1].content if 'messages' in rewrite_result else str(rewrite_result)
    print("重写后的查询:", rewrite_query)
    
    intent_result = llm_generator.query_router(rewrite_query)
    print("意图识别结果:", intent_result)
    # 从 agent 响应中提取文本内容
    intent = intent_result['messages'][-1].content.strip() if 'messages' in intent_result else str(intent_result).strip()
    print("意图:", intent)
    
    if intent == "detail":
        result = llm_generator.detail_question(rewrite_query, context,streaming=True)
        for token,meta_data in result:
            if isinstance(token, AIMessageChunk):
                print(token.content, end="", flush=True)



