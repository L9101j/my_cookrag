## 概述

`backend` 目录是 CookRag 的后端服务，提供菜谱检索与对话接口，基于 FastAPI + RAG（Retrieval-Augmented Generation）实现。后端负责：

- 解析 `dishes/` 目录下的 Markdown 菜谱文档
- 构建向量索引（如 FAISS），并存储在 `backend/temp/` 目录
- 封装大模型调用（LLM），实现问答与菜谱推荐
- 通过 RESTful API 对前端提供统一的接口

## 技术栈

- Python 3.10+
- FastAPI / Uvicorn
- FAISS / 向量检索
- SQLite 或其他关系型数据库（见 `db/`）

依赖在 `requirements.txt` 中声明。

## 目录结构说明

```bash
backend/
	config.py            # 全局配置与环境变量读取
	logging_config.py    # 日志配置
	API/                 # FastAPI 应用与路由
		main.py            # 应用入口，创建 FastAPI 实例
		dependency.py      # 依赖注入（DB、RAG 引擎等）
		schema.py          # Pydantic 模型（请求/响应体）
		routes/
			chat.py          # 聊天与问答相关接口
			surf.py          # 文档浏览或检索相关接口
	db/
		database.py        # 数据库连接与基础操作
		database_schema.sql# 初始化数据库的 SQL 脚本
	modules/             # 业务逻辑与 RAG 组件
		agent_service.py       # 对话 Agent 编排
		document_processor.py  # 文档解析与清洗
		index_construction.py  # 向量索引构建与更新
		llm_generation.py      # 大模型调用封装
		rag_engine.py          # RAG 主流程（检索 + 生成）
		retrieval_optimization.py # 检索策略优化
	temp/
		metadata.json      # 文档元数据（如文件路径、标题等）
		index.faiss/       # FAISS 索引文件
```

## 环境配置

### 1. 创建虚拟环境（可选但推荐）

在项目根目录 `CookRag/` 下：

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 环境变量

后端使用 `.env` 读取敏感配置，可以参考 `.env.example`：

- 数据库路径 / 连接串
- 大模型 API Key（如 OpenAI、Moonshot、DeepSeek 等）
- 索引目录路径

复制示例文件后按需修改：

```bash
cd backend
copy .env.example .env
```

## 启动后端服务

确认虚拟环境已激活并安装好依赖，在 `backend` 目录下运行：

```bash
uvicorn API.main:app --host 0.0.0.0 --port 8000 --reload
```

启动成功后，可以访问：

- Swagger 文档：`http://localhost:8000/docs`
- ReDoc 文档：`http://localhost:8000/redoc`

## 数据与索引初始化

在首次启动或更新 `dishes/` 目录内容后，需要：

1. 初始化数据库（如使用 `db/database_schema.sql` 建表）；
2. 通过 `modules/index_construction.py` 中的脚本构建 FAISS 索引；
3. 生成/更新 `temp/metadata.json` 与 `temp/index.faiss/`。

如果你有专门的初始化脚本（如 `test.py` 或 CLI），建议在根 README 中进一步补充使用方法。

## 主要模块说明（简要）

- `document_processor.py`：
	- 读取 `dishes/` 目录下的 Markdown 文件
	- 抽取标题、配料、步骤等结构化信息
	- 生成用于向量化的文本片段

- `index_construction.py`：
	- 调用嵌入模型生成向量
	- 构建 FAISS 索引并落盘

- `rag_engine.py`：
	- 对接检索与大模型
	- 根据用户问题召回相关菜谱片段
	- 组合为最终回复

- `agent_service.py`：
	- 封装对话 Agent 的流程（上下文管理、多轮对话等）

后续可以在 `docs/API.md` 中对具体接口进行更详细的说明。
