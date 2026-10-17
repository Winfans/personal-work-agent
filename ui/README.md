# Electron + React + Vite

Personal Work Agent 桌面客户端：

- Electron 主进程和安全 preload 使用 TypeScript
- Renderer 使用 React 19 + Vite
- 通过 NDJSON Streamable HTTP 调用 `/agent/run`
- 通过 `/api/v1/notes` 管理远程 MySQL 笔记
- 开发模式支持 Vite 热更新
- 生产模式输出到 `dist/electron` 和 `dist/renderer`

## 开发

```bash
pnpm install
pnpm electron:install
pnpm run typecheck
pnpm run dev
```

普通依赖由 pnpm 安装。Electron 运行时使用单独的国内镜像安装脚本，支持自动重试和断点续传，避免 Electron 自带 postinstall 每次失败后从头下载。

`pnpm install` 完成后会自动运行该安装器。`pnpm run dev` 和 `pnpm start` 也会在启动前检查 Electron 运行时；已安装时会立即跳过下载。

首次安装或下载中断后执行：

```bash
pnpm electron:install
```

脚本默认使用 `https://cdn.npmmirror.com/binaries/electron/`。如需临时指定其他镜像：

```bash
ELECTRON_MIRROR=https://example.com/electron/ pnpm electron:install
```

Electron 的 macOS ARM64 运行时约 106 MB。下载内容保存在 `.cache/electron/`，失败后再次执行会继续下载。

`pnpm run dev` 会同时启动 Vite 开发服务器和 Electron，不需要再打开第二个终端。React Renderer 修改后会自动热更新；Electron 主进程修改后需要重新启动开发命令。

## 构建与运行

```bash
pnpm run build
pnpm start
```

主要目录：

```text
src/electron/       Electron main 与 preload
src/renderer/       React 组件、样式与流式 API 客户端
dist/electron/      Electron TypeScript 编译结果
dist/renderer/      Vite 生产构建结果
```

## 笔记工作台

启动 Server 和 UI 后，点击左侧“工作台 → 笔记”即可：

- 加载和选择笔记
- 新建笔记
- 编辑标题与正文并保存
- 删除笔记

笔记数据由 Server 的 `/api/v1/notes` CRUD 接口读写，最终存储在 Server 配置的 MySQL 实例中。
