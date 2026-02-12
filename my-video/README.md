# 立项审批流程动画演示

<p align="center">
  <a href="https://github.com/remotion-dev/logo">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-dark.apng">
      <img alt="Animated Remotion Logo" src="https://github.com/remotion-dev/logo/raw/main/animated-logo-banner-light.gif">
    </picture>
  </a>
</p>

基于知识库中的立项申请模块业务理解，创建的用于开发团队演讲的动画演示。

## Commands

**Install Dependencies**

```console
npm i
```

**Start Preview**

```console
npm run dev
```

**Render video**

```console
npx remotion render
```

**Upgrade Remotion**

```console
npx remotion upgrade
```

## 立项审批流程动画使用说明

### 可用的动画组件

- **ProjectApprovalFlow**: 基础版立项审批流程动画 (10秒)
- **ProjectApprovalFlowDetailed**: 详细版立项审批流程动画 (15秒)，包含更多业务细节
- **ProjectApprovalFlowEnhanced**: 增强版立项审批流程动画 (15秒)，包含四个完整阶段：数据结构校验、状态流转、Kafka异步处理、要点回顾

### 构建特定视频

```bash
# 构建基础版
npx remotion render src/index.tsx ProjectApprovalFlow output-basic.mp4

# 构建详细版
npx remotion render src/index.tsx ProjectApprovalFlowDetailed output-detailed.mp4

# 构建增强版
npx remotion render src/index.tsx ProjectApprovalFlowEnhanced output-enhanced.mp4
```

### 业务流程说明

根据知识库中的立项申请模块业务理解，完整的审批流程包括：

1. **项目申请阶段**
   - 用户提交项目申请，包含预算信息、执行信息等
   - 支持独立项目和项目集立项两种类型
   - 状态：待提交 → 待确认

2. **财务确认阶段**
   - 财务人员确认预算信息，验证预算来源和金额
   - 可修改税率、公司代码、成本中心、业务范围
   - 预算预占机制确保资金可用性

3. **审批流阶段**
   - 动态审批流程，根据预算部门和金额确定审批人
   - 支持多级审批（部门负责人、平台负责人、集团负责人）
   - 与外部审批系统集成

4. **项目创建阶段**
   - 审批通过后自动创建正式项目
   - 同步预算到ERP系统
   - 完成整个立项流程

### 增强版技术架构说明

**ProjectApprovalFlowEnhanced** 组件展示了现代审批系统的技术架构：

1. **数据结构校验阶段**
   - JSON Schema验证确保数据完整性
   - 预算和权限的实时校验
   - 数据字段完整性检查

2. **状态流转阶段**
   - DRAFT → PENDING → APPROVED → COMPLETED 的完整状态机
   - 错误处理和回滚机制
   - 状态变更的原子性保证

3. **Kafka异步处理阶段**
   - 事件驱动架构，通过Kafka消息队列解耦
   - project-submission: 接收新审批请求
   - approval-events: 处理状态变更事件
   - notification-queue: 发送通知消息
   - 高吞吐量和可靠性保证

4. **要点回顾阶段**
   - 系统优势总结：实时验证、清晰状态转换、高吞吐量、容错能力
   - 最佳实践展示：事件驱动、可靠消息传递、可扩展架构

## Docs

Get started with Remotion by reading the [fundamentals page](https://www.remotion.dev/docs/the-fundamentals).

## Help

We provide help on our [Discord server](https://discord.gg/6VzzNDwUwV).

## Issues

Found an issue with Remotion? [File an issue here](https://github.com/remotion-dev/remotion/issues/new).

## License

Note that for some entities a company license is needed. [Read the terms here](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md).
