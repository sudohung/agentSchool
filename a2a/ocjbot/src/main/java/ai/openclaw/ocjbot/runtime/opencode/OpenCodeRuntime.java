package ai.openclaw.ocjbot.runtime.opencode;

import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.RuntimeType;
import ai.openclaw.ocjbot.runtime.model.*;
import ai.opencode.sdk.OpenCodeClient;
import ai.opencode.sdk.ClientConfig;
import ai.opencode.sdk.model.session.Session;
import ai.opencode.sdk.model.message.MessageWithParts;
import ai.opencode.sdk.model.event.Event;
import ai.opencode.sdk.model.event.GlobalEvent;
import ai.opencode.sdk.model.permission.PermissionInfo;
import ai.opencode.sdk.model.provider.Provider;
import ai.opencode.sdk.model.agent.Agent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

/**
 * OpenCode Runtime 实现
 * 
 * 基于 oc4j SDK，连接 OpenCode Server 提供 Agent 能力
 */
public class OpenCodeRuntime implements AgentRuntime {
    
    private static final Logger log = LoggerFactory.getLogger(OpenCodeRuntime.class);
    
    private final OpenCodeRuntimeConfig config;
    private OpenCodeClient client;
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
    private final Map<String, EventSubscriptionImpl> subscriptions = new ConcurrentHashMap<>();
    private volatile boolean initialized = false;
    
    public OpenCodeRuntime() {
        this(OpenCodeRuntimeConfig.builder().build());
    }
    
    public OpenCodeRuntime(OpenCodeRuntimeConfig config) {
        this.config = config;
    }
    
    @Override
    public void initialize() {
        if (initialized) {
            return;
        }
        
        log.info("Initializing OpenCode Runtime...");
        
        ClientConfig clientConfig = ClientConfig.builder()
            .baseUrl(config.getBaseUrl())
            .username(config.getUsername())
            .password(config.getPassword())
            .directory(config.getDirectory())
            .workspace(config.getWorkspace())
            .timeout(config.getTimeout())
            .build();
        
        this.client = new OpenCodeClient(clientConfig);
        
        RuntimeHealth health = checkHealth();
        if (!health.isHealthy()) {
            throw new RuntimeException("OpenCode Server not healthy: " + health.getMessage());
        }
        
        initialized = true;
        log.info("OpenCode Runtime initialized successfully. Connected to: {}", config.getBaseUrl());
    }
    
    @Override
    public RuntimeHealth checkHealth() {
        try {
            Map<String, Object> health = client.getGlobal().health();
            Boolean healthy = (Boolean) health.get("healthy");
            return RuntimeHealth.builder()
                .healthy(Boolean.TRUE.equals(healthy))
                .status("UP")
                .version((String) health.get("version"))
                .build();
        } catch (Exception e) {
            return RuntimeHealth.unhealthy(e.getMessage());
        }
    }
    
    @Override
    public String getName() {
        return "OpenCode Runtime";
    }
    
    @Override
    public RuntimeType getType() {
        return RuntimeType.OPENCODE;
    }
    
    // ==================== 会话管理 ====================
    
    @Override
    public RuntimeSession createSession(SessionCreateRequest request) {
        ensureInitialized();
        Session session = client.getSession().create(request.getTitle(), request.getParentId(), request.getPermissions());
        return convertSession(session);
    }
    
    @Override
    public RuntimeSession getSession(String sessionId) {
        ensureInitialized();
        Session session = client.getSession().get(sessionId);
        return convertSession(session);
    }
    
    @Override
    public List<RuntimeSession> listSessions() {
        ensureInitialized();
        List<Session> sessions = client.getSession().list();
        return sessions.stream().map(this::convertSession).toList();
    }
    
    @Override
    public boolean deleteSession(String sessionId) {
        ensureInitialized();
        return client.getSession().delete(sessionId);
    }
    
    @Override
    public SessionStatus getSessionStatus(String sessionId) {
        ensureInitialized();
        Map<String, Object> status = client.getSession().status();
        Object sessionStatus = status.get(sessionId);
        if (sessionStatus instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> ss = (Map<String, Object>) sessionStatus;
            return SessionStatus.builder()
                .sessionId(sessionId)
                .status((String) ss.getOrDefault("status", "unknown"))
                .message((String) ss.get("message"))
                .retryCount(((Number) ss.getOrDefault("retry", 0)).intValue())
                .build();
        }
        return SessionStatus.builder()
            .sessionId(sessionId)
            .status("unknown")
            .build();
    }
    
    // ==================== 消息交互 ====================
    
    @Override
    public RuntimeMessage sendMessage(String sessionId, MessageRequest request) {
        ensureInitialized();
        MessageWithParts response = client.getMessage().sendText(
            sessionId, 
            request.getText(),
            request.getProviderId(),
            request.getModelId(),
            request.getAgent(),
            false
        );
        return convertMessage(response, sessionId);
    }
    
    @Override
    public RuntimeMessage sendText(String sessionId, String text) {
        ensureInitialized();
        MessageWithParts response = client.getMessage().sendText(sessionId, text);
        return convertMessage(response, sessionId);
    }
    
    @Override
    public void sendMessageStream(String sessionId, MessageRequest request, Consumer<RuntimeEvent> eventHandler) {
        ensureInitialized();
        executor.submit(() -> {
            try {
                RuntimeMessage response = sendMessage(sessionId, request);
                eventHandler.accept(RuntimeEvent.of(sessionId, "message.complete", 
                    Map.of("messageId", response.getId())));
            } catch (Exception e) {
                eventHandler.accept(RuntimeEvent.of(sessionId, "error", 
                    Map.of("error", e.getMessage())));
            }
        });
    }
    
    @Override
    public List<RuntimeMessage> listMessages(String sessionId) {
        ensureInitialized();
        List<MessageWithParts> messages = client.getMessage().list(sessionId);
        return messages.stream()
            .map(m -> convertMessage(m, sessionId))
            .toList();
    }
    
    @Override
    public RuntimeMessage getMessage(String sessionId, String messageId) {
        ensureInitialized();
        MessageWithParts message = client.getMessage().get(sessionId, messageId);
        return convertMessage(message, sessionId);
    }
    
    // ==================== 工具执行 ====================
    
    @Override
    public ToolResult executeTool(String sessionId, ToolCallRequest request) {
        ensureInitialized();
        try {
            RuntimeMessage response = client.getMessage().shell(sessionId, request.getToolName());
            return ToolResult.success(response.getTextContent());
        } catch (Exception e) {
            return ToolResult.failure(e.getMessage());
        }
    }
    
    @Override
    public RuntimeMessage executeShell(String sessionId, String command) {
        ensureInitialized();
        MessageWithParts response = client.getMessage().shell(sessionId, command);
        return convertMessage(response, sessionId);
    }
    
    // ==================== 事件订阅 ====================
    
    @Override
    public EventSubscription subscribeEvents(Consumer<RuntimeEvent> eventHandler) {
        ensureInitialized();
        String subscriptionId = UUID.randomUUID().toString();
        EventSubscriptionImpl subscription = new EventSubscriptionImpl(
            subscriptionId, 
            () -> client.getEvent().subscribe(),
            eventHandler,
            this::convertEvent
        );
        subscriptions.put(subscriptionId, subscription);
        executor.submit(subscription::run);
        return subscription;
    }
    
    @Override
    public EventSubscription subscribeGlobalEvents(Consumer<RuntimeGlobalEvent> eventHandler) {
        ensureInitialized();
        String subscriptionId = UUID.randomUUID().toString();
        EventSubscriptionImpl subscription = new EventSubscriptionImpl(
            subscriptionId,
            () -> client.getEvent().subscribeGlobal(),
            eventHandler,
            this::convertGlobalEvent
        );
        subscriptions.put(subscriptionId, subscription);
        executor.submit(subscription::run);
        return subscription;
    }
    
    // ==================== 权限管理 ====================
    
    @Override
    public List<PermissionRequest> listPendingPermissions() {
        ensureInitialized();
        List<PermissionInfo> permissions = client.getPermission().list();
        return permissions.stream()
            .map(p -> PermissionRequest.builder()
                .id(p.getId())
                .sessionId(p.getSessionID())
                .permission(p.getPermission())
                .build())
            .toList();
    }
    
    @Override
    public boolean replyPermission(String permissionId, PermissionReply reply) {
        ensureInitialized();
        return client.getPermission().reply(permissionId, reply.getReply().name().toLowerCase(), reply.getMessage());
    }
    
    // ==================== 模型/Provider ====================
    
    @Override
    public List<RuntimeProvider> listProviders() {
        ensureInitialized();
        List<Provider> providers = client.getProvider().list();
        return providers.stream()
            .map(p -> RuntimeProvider.builder()
                .id(p.getID())
                .name(p.getName())
                .type(p.getType())
                .authenticated(true)
                .build())
            .toList();
    }
    
    @Override
    public List<RuntimeAgent> listAgents() {
        ensureInitialized();
        List<Agent> agents = client.getAgent().list();
        return agents.stream()
            .map(a -> RuntimeAgent.builder()
                .id(a.getID())
                .name(a.getName())
                .description(a.getDescription())
                .build())
            .toList();
    }
    
    // ==================== 生命周期 ====================
    
    @Override
    public void close() {
        log.info("Closing OpenCode Runtime...");
        subscriptions.values().forEach(EventSubscription::unsubscribe);
        subscriptions.clear();
        executor.shutdown();
        if (client != null) {
            client.close();
        }
        initialized = false;
        log.info("OpenCode Runtime closed.");
    }
    
    // ==================== 私有方法 ====================
    
    private void ensureInitialized() {
        if (!initialized) {
            throw new IllegalStateException("Runtime not initialized. Call initialize() first.");
        }
    }
    
    private RuntimeSession convertSession(Session session) {
        return RuntimeSession.builder()
            .id(session.getID())
            .title(session.getTitle())
            .parentId(session.getParentID())
            .workspaceId(session.getWorkspaceID())
            .state(convertSessionState(session.getStatus()))
            .createdAt(session.getCreatedAt() != null ? Instant.parse(session.getCreatedAt()) : null)
            .build();
    }
    
    private RuntimeSession.SessionState convertSessionState(String status) {
        if (status == null) return RuntimeSession.SessionState.IDLE;
        return switch (status.toLowerCase()) {
            case "busy" -> RuntimeSession.SessionState.BUSY;
            case "retry" -> RuntimeSession.SessionState.RETRY;
            case "error" -> RuntimeSession.SessionState.ERROR;
            default -> RuntimeSession.SessionState.IDLE;
        };
    }
    
    private RuntimeMessage convertMessage(MessageWithParts message, String sessionId) {
        return RuntimeMessage.builder()
            .id(message.getID())
            .sessionId(sessionId)
            .role(convertMessageRole(message.getRole()))
            .parts(convertParts(message.getParts()))
            .timestamp(message.getCreatedAt() != null ? Instant.parse(message.getCreatedAt()) : Instant.now())
            .build();
    }
    
    private RuntimeMessage.MessageRole convertMessageRole(String role) {
        if (role == null) return RuntimeMessage.MessageRole.USER;
        return switch (role.toLowerCase()) {
            case "assistant" -> RuntimeMessage.MessageRole.ASSISTANT;
            case "system" -> RuntimeMessage.MessageRole.SYSTEM;
            case "tool" -> RuntimeMessage.MessageRole.TOOL;
            default -> RuntimeMessage.MessageRole.USER;
        };
    }
    
    @SuppressWarnings("unchecked")
    private List<MessagePart> convertParts(List<?> parts) {
        if (parts == null) return List.of();
        return parts.stream()
            .map(p -> {
                if (p instanceof Map) {
                    Map<String, Object> part = (Map<String, Object>) p;
                    String type = (String) part.get("type");
                    if ("text".equals(type)) {
                        return MessagePart.text((String) part.get("text"));
                    }
                }
                return MessagePart.builder().type("unknown").content((Map<String, Object>) p).build();
            })
            .toList();
    }
    
    private RuntimeEvent convertEvent(Event event) {
        return RuntimeEvent.builder()
            .id(event.getID())
            .sessionId(event.getSessionID())
            .type(event.getType())
            .data(event.getData() != null ? event.getData() : Map.of())
            .timestamp(Instant.now())
            .build();
    }
    
    private RuntimeGlobalEvent convertGlobalEvent(GlobalEvent event) {
        return RuntimeGlobalEvent.builder()
            .id(event.getID())
            .type(event.getType())
            .data(event.getData() != null ? event.getData() : Map.of())
            .timestamp(Instant.now())
            .build();
    }
}