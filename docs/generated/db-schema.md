# 数据库 Schema 快照

- 来源：`server/src/models/note.py` 和 `server/src/database.py`
- 快照日期：2026-10-16
- 刷新方式：模型变更后检查 SQLAlchemy 元数据；尚未实现自动生成。

## `notes`

| 字段 | 类型/形式 | 约束 |
| --- | --- | --- |
| `id` | 无符号 BIGINT | 主键、自增 |
| `title` | 最长 255 字符的字符串 | 必填，带索引 |
| `content` | 文本 | 必填，默认空字符串 |
| `created_at` | 日期时间 | 数据库设置创建时间 |
| `updated_at` | 日期时间 | 数据库设置创建时间，更新时刷新 |

应用当前使用 `Base.metadata.create_all`，仓库中没有迁移历史。依赖本快照前，应核对模型代码。

