# Electron TypeScript App

一个带安全预加载桥接的最小 Electron + TypeScript 桌面应用。

## 开发

```bash
pnpm install
pnpm electron:install
pnpm run typecheck
pnpm start
```

普通依赖由 pnpm 安装。Electron 运行时使用单独的国内镜像安装脚本，支持自动重试和断点续传，避免 Electron 自带 postinstall 每次失败后从头下载。

首次安装或下载中断后执行：

```bash
pnpm electron:install
```

脚本默认使用 `https://cdn.npmmirror.com/binaries/electron/`。如需临时指定其他镜像：

```bash
ELECTRON_MIRROR=https://example.com/electron/ pnpm electron:install
```

Electron 的 macOS ARM64 运行时约 106 MB。下载内容保存在 `.cache/electron/`，失败后再次执行会继续下载。

`pnpm run dev` 会持续监听并编译 TypeScript；需要在另一个终端运行 `pnpm exec electron .` 来启动应用。
