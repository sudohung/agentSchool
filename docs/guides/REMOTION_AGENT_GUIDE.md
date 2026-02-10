# Remotion 在 AI Agent 中的使用指南

Remotion 是一个使用 React 创建视频的程序化框架。本指南介绍如何在 AI Agent（如 Claude Code、Codex、Cursor）中使用 Remotion。

## 概述

Remotion 允许开发者通过 React 组件和编程方式创建视频，充分利用 CSS、Canvas、SVG、WebGL 等 web 技术。

**核心优势**：
- 利用 web 技术栈
- 通过变量、函数、API 实现动态效果
- 复用 React 组件和生态系统

## 快速开始

### 1. 创建新项目

```bash
npx create-video@latest
```

推荐配置：
- 选择 [Blank](https://remotion.dev/templates/blank) 模板
- 启用 TailwindCSS
- 安装 Skills

### 2. 安装 Agent Skills

Remotion 维护了一套 Agent Skills，定义了在 Remotion 项目中工作的最佳实践：

```bash
npx skills add remotion-dev/skills
```

Skills 源码：https://github.com/remotion-dev/remotion/tree/main/packages/skills

### 3. 启动开发环境

```bash
cd my-video
npm install
npm run dev
```

### 4. 启动 AI Agent

在独立终端启动：

```bash
cd my-video
claude
```

现在可以通过自然语言提示创建视频了。

## 核心概念

### 基础结构

```
my-video/
├── src/
│   ├── Root.tsx          # 视频入口组件
│   ├── HelloWorld/       # 示例组件
│   └── HelloWorld.tsx
├── package.json
└── remotion.config.ts    # 配置文件
```

### 关键 API

- `Composition` - 定义视频合成
- `useVideoConfig` - 获取视频配置
- `useCurrentFrame` - 获取当前帧
- `spring` - 动画缓动函数
- `interpolate` - 插值动画

### 动画属性

```tsx
import { useSpring } from "remotion";

const MyComponent = () => {
  const progress = useSpring(0);
  return <div style={{ opacity: progress }} />;
};
```

## 渲染方式

### 本地渲染

```bash
npm run build
```

### 参数化渲染

通过 API 动态生成不同参数的视频：

```tsx
export const MyVideo = ({ title, color }) => {
  return <div style={{ backgroundColor: color }}>{title}</div>;
};
```

## 最佳实践

1. **组件复用**：将常用视觉元素提取为独立组件
2. **动画优化**：使用 `useSpring` 和 `interpolate` 实现流畅动画
3. **性能考虑**：避免在渲染循环中进行 heavy 计算
4. **类型安全**：使用 TypeScript 确保代码质量

## 官方资源

| 资源 | 链接 |
|------|------|
| 文档 | https://remotion.dev/docs |
| API 参考 | https://remotion.dev/api |
| GitHub | https://github.com/remotion-dev/remotion |
| Discord | https://remotion.dev/discord |
| 模板 | https://remotion.dev/templates |
| Showcase | https://remotion.dev/showcase |

## 相关工具

- **Remotion Studio** - 可视化编辑器 (`npm run remotion`)
- **Player** - 视频播放器组件
- **Lambda** - 云端渲染服务
- **Recorder** - 录制工具

## 注意事项

- Remotion 有特殊许可证，商业使用需获取公司许可证
- Linux 系统需要安装额外依赖包
- 推荐使用 Node.js 16+ 或 Bun 1.0.3+

## 与其他框架集成

Remotion 可以集成到现有 React 项目中：

```bash
npm install remotion
```

参考文档：[Installation in existing projects](https://remotion.dev/docs/brownfield)
