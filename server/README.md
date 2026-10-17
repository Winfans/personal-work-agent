# Python Backend

Personal Work Agent 的后端和 Agent 服务。当前包含：

- FastAPI HTTP 服务
- 健康检查接口
- Agent 请求入口与独立服务层
- TypeSafe Jev 对普通聊天与 RAG 聊天进行路由
- 阿里云百炼知识库检索
- MySQL 自动建库建表与笔记 CRUD
- 基于 LangChain 和阿里云百炼 DeepSeek v4.1 的流式文本聊天
- 基于环境变量的运行配置
- 基础接口测试

## 本地开发

先启动 MySQL（需要本机安装 Docker）：

```bash
docker compose up -d mysql
```

默认会启动 MySQL 8.4，并创建 `personal_workbench` 数据库。数据保存在 Docker Volume 中。

```bash
uv sync --extra dev
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

依赖和 Python 环境统一由 `uv` 管理，不需要手动创建或激活虚拟环境。

打开 `http://127.0.0.1:8000/docs` 查看 OpenAPI 文档。

## JSON 响应约定

普通 JSON 业务接口统一返回 `code`、`message`、`data`：

```json
{"code": 0, "message": "OK", "data": {"status": "ok", "environment": "development"}}
```

成功时 `code` 为 `0`、`message` 为 `OK`；失败时保留 HTTP 错误状态，`code` 使用同一状态码、`message` 描述错误、`data` 为 `null`。例如找不到笔记时返回 HTTP 404：

```json
{"code": 404, "message": "Note not found", "data": null}
```

删除笔记成功返回 HTTP 200，响应为 `{"code":0,"message":"OK","data":null}`。OpenAPI 文档本身不使用此业务响应结构。

`/agent/run` 和 `/chat/text` 的成功响应仍是 NDJSON 事件流；请求校验或依赖检查在流开始前失败时，返回上述 JSON 错误结构。

## Agent 流式接口

复制环境变量示例并配置百炼 API Key：

```bash
cp .env.example .env
```

启动服务后，`POST /agent/run` 接收完整消息历史，并以 NDJSON Streamable HTTP 响应逐段返回：

```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ]
}
```

响应事件顺序如下：

```text
start -> route -> [retrieval] -> delta... -> done
```

- `route`：Jev 返回 `general_chat` 或 `rag_chat`
- `retrieval`：仅 RAG 路由产生，包含召回数量与来源摘要
- `delta`：DeepSeek 流式回答片段
- `error`：任一阶段的错误

兼容接口 `POST /chat/text` 保留，但内部使用相同的 Agent 路由与生成流程。

也支持旧式单消息请求：

```json
{"message": "你好", "session_id": "optional-session-id"}
```

## 笔记 CRUD

Server 启动时会执行幂等初始化：

```sql
CREATE DATABASE IF NOT EXISTS personal_workbench;
CREATE TABLE IF NOT EXISTS notes (...);
```

创建笔记：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/notes \
  -H 'Content-Type: application/json' \
  -d '{"title":"今日计划","content":"完成个人工作台笔记功能"}'
```

查询笔记列表：

```bash
curl 'http://127.0.0.1:8000/api/v1/notes?offset=0&limit=20'
```

查询单条笔记：

```bash
curl http://127.0.0.1:8000/api/v1/notes/1
```

更新笔记：

```bash
curl -X PUT http://127.0.0.1:8000/api/v1/notes/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"更新后的标题","content":"更新后的内容"}'
```

删除笔记：

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/notes/1
```

## 测试

```bash
uv run pytest
```

## 配置

- `APP_NAME`：服务名称
- `APP_ENV`：运行环境
- `APP_HOST`：监听地址
- `APP_PORT`：监听端口
- `APP_DEBUG`：是否启用调试模式
- `DASHSCOPE_API_KEY`：阿里云百炼 API Key
- `BAILIAN_BASE_URL`：OpenAI 兼容端点
- `BAILIAN_MODEL`：模型标识，默认 `deepseek-v4.1-flash`
- `TYPESAFE_API_KEY`：TypeSafe Jev API Key
- `JEV_BASE_URL`：Jev 服务地址，默认 `https://api.typesafe.ai`
- `JEV_MODEL`：Jev 模型，默认 `jev-latest`
- `BAILIAN_RAG_BASE_URL`：百炼业务空间地址，例如 `https://llm-xxx.cn-beijing.maas.aliyuncs.com`
- `BAILIAN_RAG_INDEX_ID`：百炼知识库 ID
- `BAILIAN_RAG_TOP_K`：召回条数，默认 5
- `MYSQL_HOST`：MySQL 地址，默认 `127.0.0.1`
- `MYSQL_PORT`：MySQL 端口，默认 `3306`
- `MYSQL_USER`：MySQL 用户，开发环境默认 `root`
- `MYSQL_PASSWORD`：MySQL 密码
- `MYSQL_DATABASE`：数据库名，默认 `personal_workbench`
- `MYSQL_ECHO`：是否输出 SQL 日志，默认 `false`

路由定义集中在 `src/services/decision.py`。后续新增“生码”等类型时，可新增 Jev Choice 选项并在 `AgentService` 中增加对应处理器。
