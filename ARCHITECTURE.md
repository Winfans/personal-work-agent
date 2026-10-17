# 系统架构

Personal Work Agent 是本地桌面应用：Electron/React 负责界面，FastAPI 负责应用服务。仓库优先采用代理能够直接检查和验证的明确边界。

## 领域地图

~~~text
Electron 主进程 / preload
          │
          ▼
React 渲染进程 ── HTTP/NDJSON ──► FastAPI 路由
                                      │
                   ┌──────────────────┼──────────────────┐
                   ▼                  ▼                  ▼
               Agent 领域          笔记领域           系统领域
            路由 → 检索 → 生成      CRUD 服务          健康/配置
                   │                  │
                   ▼                  ▼
               外部服务       SQLAlchemy → MySQL
~~~

## 分层模型

预期的依赖方向：

~~~text
契约/类型 → 配置 → 仓储/数据 → 服务 → 传输/运行时 → UI
~~~

- 在外部数据进入系统的边界进行验证。
- 路由适配 HTTP，不承载业务逻辑。
- 服务应能脱离 HTTP 请求独立调用。
- 持久化细节不进入渲染进程。
- 已有专用客户端模块时，UI 组件不直接解析原始传输数据。
- 跨领域协作通过明确契约进行，避免跨层深度导入。

这些规则目前只有文档约束，尚无专用架构检查器；见 [质量评估](docs/QUALITY_SCORE.md)。

## 桌面端

- `ui/src/electron/main.ts`：窗口和 Electron 生命周期。
- `ui/src/electron/preload.ts`：向渲染进程提供最小桥接接口。
- `ui/src/renderer/App.tsx`：聊天状态与主导航。
- `ui/src/renderer/NotesPage.tsx`：笔记列表与编辑状态。
- `ui/src/renderer/*-api.ts`：后端 HTTP 请求和流解析。

渲染进程当前假定后端地址为 `127.0.0.1:8000`。服务商与数据库凭证只保留在后端进程。

## Agent 领域

- `server/src/api/routes/agent.py`：主要流式接口。
- `server/src/api/routes/chat.py`：兼容接口。
- `server/src/services/agent.py`：流程编排。
- `server/src/services/decision.py`：`general_chat` / `rag_chat` 分类路由。
- `server/src/services/rag.py`：私有知识检索。
- `server/src/services/chat.py`：模型生成。

流式契约为 `start → route → retrieval? → delta* → done`，中途失败产生 `error`。详见[聊天产品规格](docs/product-specs/chat.md)和[设计记录 0002](docs/design-docs/0002-agent-stream-protocol.md)。

普通 JSON 业务接口使用统一的 `code`、`message`、`data` 响应结构；流开始前的错误也遵循此结构。NDJSON 事件流保持独立协议，详见[设计记录 0004](docs/design-docs/0004-json-response-envelope.md)。

## 笔记领域

- 路由和 schema 在 `/api/v1/notes` 下提供 CRUD。
- `NoteService` 负责持久化操作。
- 异步 SQLAlchemy 会话连接 MySQL。
- 后端目前在应用生命周期启动阶段初始化数据库及数据表。

该功能已存在于当前工作区，但尚缺少 MySQL 和 Electron 的运行验证证据；见[执行中的计划](docs/exec-plans/active/notes-workbench.md)。

## 依赖边界

允许的依赖：

- 渲染进程组件 → 渲染进程 API 客户端及类型。
- FastAPI 路由 → schema、service、依赖项。
- service → 契约、配置、持久化接口。
- database 层 → model、配置。

禁止的依赖：

- 渲染进程 → 服务商/数据库凭证或直接数据库访问。
- model/database → HTTP 路由或 UI。
- 默认测试 → 真实服务商或生产数据。
- 绕过 service 或已记录契约的跨领域导入。

## 运行与验证

安装方式见两个组件的 README。常规本地检查：

~~~bash
cd server && uv run pytest
cd ui && pnpm run typecheck
cd ui && pnpm run build
git diff --check
~~~

MySQL、外部服务及桌面交互需要单独的集成验证，不能依据单元测试或构建结果推断成功。

## 已知缺口

- 缺少依赖边界检查器和仓库级统一 `check` 命令。
- 缺少 MySQL schema 迁移机制和会话持久化。
- 后端地址、打包、升级及凭证存储尚未产品化。
- 外部服务降级、重试、日志脱敏、链路追踪和指标尚不完整。
