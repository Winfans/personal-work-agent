# 多会话聊天历史可恢复

- 状态：执行中
- 负责人：Codex
- 创建/更新日期：2026-10-17
- 相关架构、设计与规格：`ARCHITECTURE.md`、`docs/product-specs/chat.md`

## 目标结果

聊天会话和完整消息持久化在 MySQL；桌面端能查看多个会话、按需加载历史、切换并继续聊天。

## 当前状态与证据

`App.tsx` 仅在组件状态保存消息；MySQL 当前只存笔记。`/agent/run` 由客户端提交消息历史，不负责持久化。

## 范围与非目标

新增会话与消息模型、JSON 列表/详情接口、持久化流式聊天接口及对应 UI。保留旧 `/agent/run`、`/chat/text` 行为。不处理跨设备用户身份、全文搜索或删除会话。

## 约束及必须保持的规则

非流式接口使用 `{code,message,data}`；NDJSON 保持 `start → route → retrieval? → delta* → done` 或 `error`。不连接真实外部服务运行默认测试。

## 里程碑

1. 建立 MySQL 会话、消息表与服务测试。
2. 增加会话 API 和持久化流式接口。
3. UI 展示会话列表、按批加载消息并支持继续聊天。
4. 更新权威文档并运行检查。

## 验证计划

| 检查项 | 命令或步骤 | 预期证据 |
| --- | --- | --- |
| 后端 | `cd server && uv run pytest` | 全部通过 |
| 前端 | `cd ui && pnpm run typecheck && pnpm run build` | 全部通过 |
| 补丁 | `git diff --check` | 无空白错误 |

## 风险、回滚与恢复

当前没有 schema 迁移系统，新表由启动时的 `create_all` 创建；生产数据需要独立备份。流失败时用户消息保留，未完成的助手回答不入库。

## 决策记录

- 2026-10-17：完整历史以关系表持久化，列表与消息分页读取；推理只取最近 100 条上下文，避免无界请求。

## 进度记录

- 2026-10-17：已实现会话/消息模型、JSON 与 NDJSON 接口、UI 历史列表与消息分页。
- 2026-10-17：后端 13 项测试通过；前端类型检查和生产构建通过；`git diff --check` 通过。环境中没有 `docker` 或 `mysql` 命令，尚不能执行真实 MySQL 重启恢复验证。

## 验收标准

- [ ] 可创建多个会话，重启后仍可列出。
- [ ] 每个会话的用户消息与已完成助手回答均可恢复。
- [ ] 切换会话可加载近期消息和更早历史，并继续发送。
- [x] 旧接口契约和默认测试不回归。

## 完成证据

`UV_CACHE_DIR=/private/tmp/pwa-uv-cache uv run pytest`：13 passed；`pnpm run typecheck` 和 `pnpm run build` 成功；MySQL DDL 在 MySQL 方言下编译成功。真实 MySQL 持久化和 Electron 交互仍待运行验证。
