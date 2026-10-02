/**
 * agentBot 应用入口
 * 装配流程：
 *  1. 校验配置
 *  2. 初始化飞书客户端/服务
 *  3. 初始化 Agent 注册表 + 会话管理器
 *  4. 启动 OpenCode 事件监听（后台运行）
 *  5. 启动飞书长连接网关（前台运行）
 */

import * as lark from '@larksuiteoapi/node-sdk';
// 全局 fetch 超时配置须最先执行（OpenCode 长推理任务依赖，见模块注释）
import './config/fetch-dispatcher.js';
import { BotConfig } from './config/bot-config.js';
import { ChatService } from './feishu/chat-service.js';
import { FeishuGateway } from './feishu/feishu-gateway.js';
import { AgentRegistry } from './agent/agent-registry.js';
import { SessionManager } from './agent/session-manager.js';
import { RoleRegistry } from './agent/role-registry.js';
import { InstancePool } from './agent/instance-pool.js';
import { MessageHandler } from './handlers/message-handler.js';
import { OpencodeListener } from './events/opencode-listener.js';
import { AdminServer } from './admin/admin-server.js';
import { ApiSessionManager } from './api/api-session-manager.js';
import { TaskQueue } from './api/task-queue.js';
import { McpServer } from './api/mcp-server.js';

// ==================== 步骤1：配置校验 ====================
if (!BotConfig.isValid()) {
    console.error('[agentBot] 缺少必要环境变量：FEISHU_APP_ID / FEISHU_APP_SECRET');
    console.error('[agentBot] 请复制 .env.example 为 .env 并填写配置');
    process.exit(1);
}

// ==================== 步骤2：飞书服务 ====================
const larkClient = new lark.Client({
    appId: BotConfig.appId,
    appSecret: BotConfig.appSecret,
});
const chatService = new ChatService(larkClient);

// ==================== 步骤3：Agent 层 ====================
const registry = new AgentRegistry();
const sessionManager = new SessionManager(registry);

// ==================== 步骤4：事件监听（后台） ====================
// 职能注册表 + 实例池 + Agent API 通道（供其他智能体经 MCP 调用）
const roleRegistry = new RoleRegistry();
const instancePool = new InstancePool(roleRegistry);
const apiSessions = new ApiSessionManager(roleRegistry, instancePool);
const apiTasks = new TaskQueue(apiSessions, instancePool, roleRegistry);
apiSessions.startSweeper();
apiTasks.startSweeper();

// API 会话的 question/permission 事件路由（与飞书交互链路隔离）
const apiRouter = {
    hasSession: (internalSessionId) => apiSessions.hasInternalSession(internalSessionId),
    onQuestionAsked: (properties) => apiTasks.onQuestionAsked(properties),
    onPermissionAsked: (properties) => apiTasks.onPermissionAsked(properties),
};

// getClient 每次重连时取最新客户端，支持配置页修改服务地址后自动切换
const listener = new OpencodeListener({
    getClient: () => registry.getClient(),
    sessionManager,
    chatService,
    apiRouter,
});
listener.start().catch((error) => {
    console.error('[agentBot] OpenCode 事件监听异常退出:', error);
    // 事件流断开不影响消息通道，仅告警
});

// ==================== 步骤5：消息处理 + 飞书网关（前台） ====================
const interaction = listener.getInteraction();

const messageHandler = new MessageHandler({
    sessionManager,
    registry,
    chatService,
    interaction,
});

const gateway = new FeishuGateway({
    appId: BotConfig.appId,
    appSecret: BotConfig.appSecret,
    messageTtl: BotConfig.messageConfig.messageIdTtl,
    expiryTime: BotConfig.messageConfig.messageExpiryTime,
    logLevel: BotConfig.logConfig.level,
});

// 第二个回调：卡片按钮点击（card.action.trigger），用于 question 选项闭环
gateway.start(
    (chatId, text, messageContext) => messageHandler.handle(chatId, text, messageContext),
    (cardAction) => interaction.handleCardAction(cardAction),
);

// 优雅退出
process.on('SIGINT', () => {
    console.log('[agentBot] 收到退出信号，正在关闭...');
    process.exit(0);
});

// ==================== 步骤6：配置管理页（8081） ====================
const adminServer = new AdminServer({
    registry,
    gateway,
    roleRegistry,
    instancePool,
    port: parseInt(process.env.ADMIN_PORT || '8081', 10),
});
adminServer.start();

// ==================== 步骤7：MCP Agent API 服务（8082） ====================
const mcpServer = new McpServer({
    roleRegistry,
    sessions: apiSessions,
    tasks: apiTasks,
    port: parseInt(process.env.MCP_PORT || '8082', 10),
});
mcpServer.start();
