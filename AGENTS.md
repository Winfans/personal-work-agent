# Personal Work Agent — 代理工作指南

Personal Work Agent 是由 Electron/React 客户端和 FastAPI 服务组成的本地工作台，提供流式聊天、请求路由、可选的知识库检索及 MySQL 笔记功能。

## 从这里开始

- 文档索引与权威来源：[`docs/README.md`](docs/README.md)
- 当前系统边界：[`ARCHITECTURE.md`](ARCHITECTURE.md)
- 设计目录与原则：[`docs/design-docs/index.md`](docs/design-docs/index.md)
- 执行中的计划：[`docs/exec-plans/active/`](docs/exec-plans/active/)
- 产品行为：[`docs/product-specs/index.md`](docs/product-specs/index.md)
- 质量缺口：[`docs/QUALITY_SCORE.md`](docs/QUALITY_SCORE.md)
- 组件运行说明：[`server/README.md`](server/README.md)、[`ui/README.md`](ui/README.md)

局部的小改动只需阅读相关代码、测试和架构章节。跨组件或跨会话的工作应按 [`docs/exec-plans/TEMPLATE.md`](docs/exec-plans/TEMPLATE.md) 编写可持续更新的计划。

## 仓库地图

- `server/`：由 `uv` 管理的 FastAPI 服务。
- `server/src/api/routes/`：HTTP 入口与依赖注入。
- `server/src/services/`：业务逻辑与 Agent 编排。
- `server/src/schemas/`：API 数据契约。
- `server/src/models/`、`server/src/database.py`：数据持久化。
- `server/tests/`：隔离运行的后端测试。
- `ui/src/electron/`：Electron 主进程与 preload。
- `ui/src/renderer/`：React 界面与专用 HTTP 客户端。

## 必须保持的约束

- 保留用户尚未提交及与当前任务无关的改动。
- 保持流式事件顺序：`start`、`route`、可选 `retrieval`、若干 `delta`、`done`；失败时使用 `error`。
- 普通 JSON 业务接口使用 `code`、`message`、`data` 结构；成功时为 `0`、`OK`，流式 NDJSON 接口保持事件格式。
- 除非明确批准破坏性变更，保持 `/chat/text` 与主要 Agent 流程兼容。
- 路由处理 HTTP，schema 验证数据，service 承载行为，model 和 database 模块管理持久化。
- UI 的网络请求放在专用 API 模块中；组件管理展示与交互状态。
- 默认测试不连接真实模型、路由、RAG、数据库或部署服务；不要提交凭证。
- 提交、推送、部署或破坏性数据操作需要明确授权。

## 验证命令

~~~bash
cd server && uv run pytest
cd ui && pnpm run typecheck
cd ui && pnpm run build
git diff --check
~~~

MySQL 运行验证需要单独配置 Docker 服务。仅做类型检查时不需要安装 Electron 运行时。

架构或行为变化时，同步更新对应的权威文档。长期有效的设计原因写入 `docs/design-docs/`；执行过程与进度写入 `docs/exec-plans/`。
