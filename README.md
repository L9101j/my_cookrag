## 项目简介

CookRag 是一个面向「菜谱知识库 + 智能助手」的 RAG（Retrieval-Augmented Generation）项目：

- 使用本地 `dishes/` 目录中的 Markdown 菜谱作为知识库
- 后端通过向量检索 + 大模型实现智能问答与菜谱推荐
- 前端提供对话、历史和菜谱展示的 Web 界面

你可以像和助手聊天一样提问，例如：

- “帮我推荐一个简单的晚餐，最好 30 分钟内能做好的。”
- “我只有鸡蛋、番茄和面条，可以做什么？”

## 仓库结构

```bash
CookRag/
	backend/        # Python 后端服务（FastAPI + RAG 引擎）
	fronted/
		cookrag/      # Vue 3 前端 SPA 应用
	dishes/         # 菜谱知识库（Markdown 文件，按类别整理）
	docs/           # 设计与接口文档（architecture.md、API.md 等）
	logs/           # 运行日志（可选）
	test.py         # 与索引/初始化相关的测试或脚本（视实现而定）
```

更细致的前后端说明分别见：

- `backend/README.md`
- `fronted/cookrag/README.md`

## 核心流程概览

1. **文档准备**：
	 - 在 `dishes/` 目录中以 Markdown 形式维护菜谱
	 - 可按类别（`breakfast/`、`meat_dish/`、`dessert/` 等）组织

2. **索引构建**（离线）
	 - 后端模块读取 `dishes/` 中的文档
	 - 对文本进行清洗、分段与向量化
	 - 使用 FAISS 构建向量索引，存储在 `backend/temp/index.faiss/` 中
	 - 生成 `metadata.json` 记录文件路径、标题等信息

3. **在线检索与问答**
	 - 前端调用后端聊天接口（如 `/chat`）
	 - 后端基于用户问题在向量索引中检索相关菜谱片段
	 - 将检索结果与问题一起发送给大模型，生成回答
	 - 前端展示自然语言回答，并可展示对应菜谱内容

## 快速开始

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd CookRag
```

### 2. 启动后端

详见 `backend/README.md`，典型流程：

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env  # 根据需要修改
uvicorn API.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

详见 `fronted/cookrag/README.md`，典型流程：

```bash
cd fronted\\cookrag
npm install
npm run dev
```

默认访问：`http://localhost:5173/`

## 索引与数据管理

- 首次运行前建议完成索引构建（可通过专门脚本或在 `backend/modules/index_construction.py` 中实现）
- 当 `dishes/` 中菜谱有较大更新时，需要重新构建或增量更新向量索引


