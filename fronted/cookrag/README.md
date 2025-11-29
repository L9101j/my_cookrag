## 概述

`fronted/cookrag` 是 CookRag 项目的前端单页应用，基于 **Vue 3 + TypeScript + Vite** 构建，用于：

- 提供对话式菜谱查询界面（如聊天页 `Chat.vue`）
- 展示历史记录（如 `History.vue`）
- 展示推荐或检索到的菜谱内容（如 `Recipe.vue`）

前端通过 HTTP 调用后端 API（`backend` 服务），实现 RAG 智能检索与问答。

## 技术栈

- Vue 3 + Composition API
- TypeScript
- Vite 开发/构建工具
- Axios 等 HTTP 请求库（见 `src/service/api.ts`）

详细依赖见 `package.json`。

## 目录结构

```bash
fronted/cookrag/
  src/
    main.ts         # 入口文件，挂载 Vue 应用
    App.vue         # 根组件与路由布局
    service/
      api.ts        # 与后端交互的 API 封装
    views/
      Chat.vue      # 与 RAG 后端对话的聊天页面
      History.vue   # 对话/查询历史记录页面
      Recipe.vue    # 菜谱详情或推荐展示页面
    assets/         # 静态资源、样式等
  vite.config.ts    # Vite 配置
  tsconfig*.json    # TypeScript 配置
```

## 开发环境准备

### 1. 安装 Node.js

建议使用 Node.js 18+。可以通过 `node -v` 查看当前版本。

### 2. 安装依赖

在 `fronted/cookrag` 目录下执行：

```bash
npm install
```

## 启动开发服务器

在 `fronted/cookrag` 目录下：

```bash
npm run dev
```

默认情况下，Vite 会在 `http://localhost:5173/` 启动开发服务器。

如需与后端联调，请确认：

- 后端 FastAPI 服务已在 `http://localhost:8000` 运行（或其他地址）；
- `src/service/api.ts` 中的基础 URL（baseURL）指向正确的后端地址；
- 如有跨域需求，后端已配置 CORS。

## 构建生产版本

在 `fronted/cookrag` 目录下：

```bash
npm run build
```

打包产物将生成在 `dist/` 目录下，可部署到任意静态文件服务器（如 Nginx、Vercel、Netlify 等）。

## 推荐 IDE 设置

- VS Code + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)
- 关闭旧版 Vetur 插件，避免类型冲突

## 与后端的交互约定（简要）

前端通过 `src/service/api.ts` 调用后端 API，一般流程为：

1. 用户在 `Chat.vue` 输入问题
2. 通过 `api.ts` 调用后端 `/chat` 等接口
3. 后端基于 RAG 引擎检索 `dishes/` 菜谱并调用大模型生成答案
4. 前端展示回答，并可在 `Recipe.vue` 中展示相关菜谱细节

更详细的接口说明可参见项目根目录下的 `docs/API.md`。
