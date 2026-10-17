# 前端指南

## 界面组成

- Electron 主进程和 preload 提供桌面外壳。
- React 渲染进程提供聊天及笔记工作台。
- `agent-api.ts` 解析 NDJSON 流。
- `notes-api.ts` 负责笔记 CRUD 请求。

## 交互原则

- 让流式生成和取消操作的状态可见且结果明确。
- 保持输入法行为：非输入法组合状态下 Enter 发送；Shift+Enter 换行。
- 错误信息应可操作，不得暴露后端凭证或私有服务响应。
- 组件应呈现加载、空状态、选中、保存和失败状态。
- 删除等破坏性用户操作需要确认。

## 验证

~~~bash
pnpm run typecheck
pnpm run build
~~~

这些检查不能证明 Electron 的运行交互正确。运行时可用时，用户可见变更还需执行交互冒烟验证。项目目前没有自动化的浏览器或 Electron 交互测试；此缺口记录在质量评估中。

