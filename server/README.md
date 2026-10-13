# Python Backend

Personal Work Agent 的后端和 Agent 服务。当前包含：

- FastAPI HTTP 服务
- 健康检查接口
- Agent 请求入口与独立服务层
- 基于 LangChain 和阿里云百炼 DeepSeek v4.1 的流式文本聊天
- 基于环境变量的运行配置
- 基础接口测试

## 本地开发

```bash
uv sync --extra dev
uv run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

依赖和 Python 环境统一由 `uv` 管理，不需要手动创建或激活虚拟环境。

打开 `http://127.0.0.1:8000/docs` 查看 OpenAPI 文档。

## 文本聊天

复制环境变量示例并配置百炼 API Key：

```bash
cp .env.example .env
```

启动服务后，`POST /chat/text` 接收完整消息历史，并以 NDJSON Streamable HTTP 响应逐段返回：

```json
{
  "messages": [
    {"role": "user", "content": "你好"}
  ]
}
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

`src/services/agent.py` 是后续接入模型、工具和持久化能力的扩展点。
