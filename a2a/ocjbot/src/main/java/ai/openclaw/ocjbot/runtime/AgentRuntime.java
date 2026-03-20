package ai.openclaw.ocjbot.runtime;

import ai.openclaw.ocjbot.runtime.model.*;

import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

/**
 * Agent Runtime 抽象接口
 * 
 * 定义 Agent 运行时的核心能力，不同的底层实现可以互换：
 * - OpenCodeRuntime: 基于 oc4j SDK，连接 OpenCode Server
 * - DirectLLMRuntime: 直接调用 OpenAI/Anthropic API
 * - MockRuntime: 测试用 Mock 实现
 */
public interface AgentRuntime extends AutoCloseable {

    // ==================== 生命周期 ====================
    
    /**
     * 初始化运行时
     */
    void initialize();
    
    /**
     * 检查运行时健康状态
     */
    RuntimeHealth checkHealth();
    
    /**
     * 获取运行时名称
     */
    String getName();
    
    /**
     * 获取运行时类型
     */
    RuntimeType getType();

    // ==================== 会话管理 ====================
    
    /**
     * 创建新会话
     */
    RuntimeSession createSession(SessionCreateRequest request);
    
    /**
     * 获取会话
     */
    RuntimeSession getSession(String sessionId);
    
    /**
     * 列出所有会话
     */
    List<RuntimeSession> listSessions();
    
    /**
     * 删除会话
     */
    boolean deleteSession(String sessionId);
    
    /**
     * 获取会话状态
     */
    SessionStatus getSessionStatus(String sessionId);

    // ==================== 消息交互 ====================
    
    /**
     * 发送消息并等待回复
     */
    RuntimeMessage sendMessage(String sessionId, MessageRequest request);
    
    /**
     * 发送文本消息
     */
    RuntimeMessage sendText(String sessionId, String text);
    
    /**
     * 发送消息并流式接收响应
     */
    void sendMessageStream(String sessionId, MessageRequest request, Consumer<RuntimeEvent> eventHandler);
    
    /**
     * 列出会话消息
     */
    List<RuntimeMessage> listMessages(String sessionId);
    
    /**
     * 获取消息详情
     */
    RuntimeMessage getMessage(String sessionId, String messageId);

    // ==================== 工具执行 ====================
    
    /**
     * 执行工具
     */
    ToolResult executeTool(String sessionId, ToolCallRequest request);
    
    /**
     * 执行 Shell 命令
     */
    RuntimeMessage executeShell(String sessionId, String command);

    // ==================== 事件订阅 ====================
    
    /**
     * 订阅事件流
     */
    EventSubscription subscribeEvents(Consumer<RuntimeEvent> eventHandler);
    
    /**
     * 订阅全局事件
     */
    EventSubscription subscribeGlobalEvents(Consumer<RuntimeGlobalEvent> eventHandler);

    // ==================== 权限管理 ====================
    
    /**
     * 列出待处理的权限请求
     */
    List<PermissionRequest> listPendingPermissions();
    
    /**
     * 回复权限请求
     */
    boolean replyPermission(String permissionId, PermissionReply reply);
    
    // ==================== 模型/Provider ====================
    
    /**
     * 列出可用的 Provider
     */
    List<RuntimeProvider> listProviders();
    
    /**
     * 获取 Agent 列表
     */
    List<RuntimeAgent> listAgents();
}