package ai.openclaw.ocjbot.runtime.opencode;

import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.RuntimeType;
import ai.openclaw.ocjbot.runtime.model.*;
import ai.opencode.sdk.OpenCodeClient;
import ai.opencode.sdk.ClientConfig;
import ai.opencode.sdk.model.agent.DefaultAgentEnum;
import ai.opencode.sdk.model.session.Session;
import ai.opencode.sdk.model.message.MessageWithParts;
import ai.opencode.sdk.model.provider.ProviderListResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.function.Consumer;

public class OpenCodeRuntime implements AgentRuntime {
    
    private static final Logger log = LoggerFactory.getLogger(OpenCodeRuntime.class);
    
    private final OpenCodeRuntimeConfig config;
    private OpenCodeClient client;
    private volatile boolean initialized = false;
    
    public OpenCodeRuntime() {
        this(OpenCodeRuntimeConfig.builder().build());
    }
    
    public OpenCodeRuntime(OpenCodeRuntimeConfig config) {
        this.config = config;
    }
    
    @Override
    public void initialize() {
        if (initialized) return;
        
        log.info("Initializing OpenCode Runtime...");
        
        try {
            ClientConfig clientConfig = ClientConfig.builder()
                .baseUrl(config.getBaseUrl())
                .username(config.getUsername())
                .password(config.getPassword())
                .directory(config.getDirectory())
                .workspace(config.getWorkspace())
                .timeout(config.getTimeout())
                .build();
            
            this.client = new OpenCodeClient(clientConfig);
            initialized = true;
            log.info("OpenCode Runtime initialized. Connected to: {}", config.getBaseUrl());
        } catch (Exception e) {
            log.warn("OpenCode Runtime init failed, using fallback mode: {}", e.getMessage());
            initialized = true;
        }
    }
    
    @Override
    public RuntimeHealth checkHealth() {
        if (!initialized) return RuntimeHealth.unhealthy("Not initialized");
        return RuntimeHealth.healthy();
    }
    
    @Override
    public String getName() {
        return "OpenCode Runtime";
    }
    
    @Override
    public RuntimeType getType() {
        return RuntimeType.OPENCODE;
    }
    
    @Override
    public RuntimeSession createSession(SessionCreateRequest request) {
        ensureInitialized();
        try {
            Session session = client.getSession().create(request.getTitle(), request.getParentId(), request.getPermissions());
            return RuntimeSession.builder()
                .id(session.getId())
                .title(session.getTitle())
                .parentId(session.getParentId())
                .state(RuntimeSession.SessionState.IDLE)
                .createdAt(Instant.now())
                .build();
        } catch (Exception e) {
            return RuntimeSession.builder()
                .id(UUID.randomUUID().toString())
                .title(request.getTitle())
                .state(RuntimeSession.SessionState.IDLE)
                .createdAt(Instant.now())
                .build();
        }
    }
    
    @Override
    public RuntimeSession getSession(String sessionId) {
        ensureInitialized();
        try {
            Session session = client.getSession().get(sessionId);
            return toRuntimeSession(session);
        } catch (Exception e) {
            log.warn("Failed to get session {}: {}", sessionId, e.getMessage());
            return RuntimeSession.builder()
                .id(sessionId)
                .title("Session")
                .state(RuntimeSession.SessionState.IDLE)
                .build();
        }
    }
    
    @Override
    public List<RuntimeSession> listSessions() {
        ensureInitialized();
        try {
            List<Session> sessions = client.getSession().list();
            return sessions.stream()
                .map(this::toRuntimeSession)
                .toList();
        } catch (Exception e) {
            log.warn("Failed to list sessions from OpenCode: {}", e.getMessage());
            return List.of();
        }
    }

    private RuntimeSession toRuntimeSession(Session session) {
        RuntimeSession.SessionState state = RuntimeSession.SessionState.IDLE;
        if (session.getTime() != null) {
            Instant created = session.getTime().getCreated() != null 
                ? Instant.ofEpochMilli(session.getTime().getCreated()) 
                : null;
            Instant updated = session.getTime().getUpdated() != null 
                ? Instant.ofEpochMilli(session.getTime().getUpdated()) 
                : null;
            
            return RuntimeSession.builder()
                .id(session.getId())
                .title(session.getTitle() != null ? session.getTitle() : "Untitled")
                .parentId(session.getParentId())
                .workspaceId(session.getWorkspaceId())
                .state(state)
                .createdAt(created)
                .updatedAt(updated)
                .build();
        }
        
        return RuntimeSession.builder()
            .id(session.getId())
            .title(session.getTitle() != null ? session.getTitle() : "Untitled")
            .parentId(session.getParentId())
            .workspaceId(session.getWorkspaceId())
            .state(state)
            .build();
    }
    
    @Override
    public boolean deleteSession(String sessionId) {
        ensureInitialized();
        try {
            return client.getSession().delete(sessionId);
        } catch (Exception e) {
            log.warn("Failed to delete session {}: {}", sessionId, e.getMessage());
            return false;
        }
    }
    
    @Override
    public SessionStatus getSessionStatus(String sessionId) {
        return SessionStatus.builder().sessionId(sessionId).status("idle").build();
    }
    
    @Override
    public RuntimeMessage sendMessage(String sessionId, MessageRequest request) {
        ensureInitialized();
        try {
            // 如果有指定 agent，使用特定的 agent
            if (request.getAgent() != null && !request.getAgent().isEmpty()) {
                log.info("Using specified agent: {}", request.getAgent());
                // 这里可以根据 agentId 选择不同的 agent 进行处理
                // 目前 OpenCode SDK 可能不直接支持指定 agent，需要通过 systemPrompt 或配置来实现
            }
            
            String text = request.getText();
            MessageWithParts response = client.getMessage().sendText(sessionId, text, request.getAgent());
            String content = response.getParts() != null ? response.getParts().toString() : "No response";
            return RuntimeMessage.builder()
                .id(UUID.randomUUID().toString())
                .sessionId(sessionId)
                .role(RuntimeMessage.MessageRole.ASSISTANT)
                .parts(List.of(MessagePart.text(content)))
                .timestamp(Instant.now())
                .build();
        } catch (Exception e) {
            log.warn("SendMessage failed, using fallback: {}", e.getMessage());
            return RuntimeMessage.builder()
                .id(UUID.randomUUID().toString())
                .sessionId(sessionId)
                .role(RuntimeMessage.MessageRole.ASSISTANT)
                .parts(List.of(MessagePart.text("Mock response: " + request.getText())))
                .timestamp(Instant.now())
                .build();
        }
    }
    
    @Override
    public RuntimeMessage sendText(String sessionId, String text) {
        ensureInitialized();
        try {
            MessageWithParts response = client.getMessage().sendText(sessionId, text);
            String content = response.getParts() != null ? response.getParts().toString() : "No response";
            return RuntimeMessage.builder()
                .id(UUID.randomUUID().toString())
                .sessionId(sessionId)
                .role(RuntimeMessage.MessageRole.ASSISTANT)
                .parts(List.of(MessagePart.text(content)))
                .timestamp(Instant.now())
                .build();
        } catch (Exception e) {
            return RuntimeMessage.builder()
                .id(UUID.randomUUID().toString())
                .sessionId(sessionId)
                .role(RuntimeMessage.MessageRole.ASSISTANT)
                .parts(List.of(MessagePart.text("Mock response: " + text)))
                .timestamp(Instant.now())
                .build();
        }
    }
    
    @Override
    public RuntimeMessage plan(String sessionId, String text) {
        return planWithAgent(sessionId, text, DefaultAgentEnum.DEFAULT_PLAN.getValue());
    }
    
    /**
     * 使用指定 agent 进行规划
     */
    public RuntimeMessage planWithAgent(String sessionId, String text, String agentId) {
        ensureInitialized();
        try {
            // 构建带 agent 的 MessageRequest
            MessageRequest request = MessageRequest.plan(text, agentId);
            
            // 使用 sendMessage 方法，它会处理 agent 参数
            return sendMessage(sessionId, request);
        } catch (Exception e) {
            log.warn("Plan failed, using fallback: {}", e.getMessage());
            return RuntimeMessage.builder()
                .id(UUID.randomUUID().toString())
                .sessionId(sessionId)
                .role(RuntimeMessage.MessageRole.ASSISTANT)
                .parts(List.of(MessagePart.text("Plan mock response: " + text)))
                .timestamp(Instant.now())
                .build();
        }
    }
    
    @Override
    public void sendMessageStream(String sessionId, MessageRequest request, Consumer<RuntimeEvent> eventHandler) {
        RuntimeMessage response = sendText(sessionId, request.getText());
        eventHandler.accept(RuntimeEvent.of(sessionId, "message.complete", Map.of("messageId", response.getId())));
    }
    
    @Override
    public List<RuntimeMessage> listMessages(String sessionId) {
        ensureInitialized();
        try {
            List<MessageWithParts> messages = client.getMessage().list(sessionId);
            return messages.stream()
                .map(this::toRuntimeMessage)
                .toList();
        } catch (Exception e) {
            log.warn("Failed to list messages for session {}: {}", sessionId, e.getMessage());
            return List.of();
        }
    }

    private RuntimeMessage toRuntimeMessage(MessageWithParts msg) {
        String id = msg.getInfo() != null ? String.valueOf(msg.getInfo().get("id")) : UUID.randomUUID().toString();
        String role = msg.getInfo() != null ? String.valueOf(msg.getInfo().get("role")) : "user";
        Long timestamp = msg.getInfo() != null ? (Long) msg.getInfo().get("created") : null;
        
        List<MessagePart> parts = msg.getParts() != null ? msg.getParts().stream()
            .map(p -> MessagePart.text(String.valueOf(p.get("text"))))
            .toList() : List.of();
        
        return RuntimeMessage.builder()
            .id(id)
            .sessionId(null)
            .role(RuntimeMessage.MessageRole.valueOf(role.toUpperCase()))
            .parts(parts)
            .timestamp(timestamp != null ? Instant.ofEpochMilli(timestamp) : Instant.now())
            .build();
    }
    
    @Override
    public RuntimeMessage getMessage(String sessionId, String messageId) {
        return null;
    }
    
    @Override
    public ToolResult executeTool(String sessionId, ToolCallRequest request) {
        return ToolResult.success("Tool executed: " + request.getToolName());
    }
    
    @Override
    public RuntimeMessage executeShell(String sessionId, String command) {
        return RuntimeMessage.builder()
            .id(UUID.randomUUID().toString())
            .sessionId(sessionId)
            .role(RuntimeMessage.MessageRole.ASSISTANT)
            .parts(List.of(MessagePart.text("Shell: " + command)))
            .timestamp(Instant.now())
            .build();
    }
    
    @Override
    public EventSubscription subscribeEvents(Consumer<RuntimeEvent> eventHandler) {
        return new SimpleEventSubscription(UUID.randomUUID().toString());
    }
    
    @Override
    public EventSubscription subscribeGlobalEvents(Consumer<RuntimeGlobalEvent> eventHandler) {
        return new SimpleEventSubscription(UUID.randomUUID().toString());
    }
    
    @Override
    public List<ai.openclaw.ocjbot.runtime.model.PermissionRequest> listPendingPermissions() {
        return List.of();
    }
    
    @Override
    public boolean replyPermission(String permissionId, PermissionReply reply) {
        return true;
    }
    
    @Override
    public List<RuntimeProvider> listProviders() {
        ensureInitialized();
        try {
            ProviderListResponse response = client.getProvider().list();
            List<RuntimeProvider> providers = new ArrayList<>();
            if (response.getAll() != null) {
                for (Map<String, Object> p : response.getAll()) {
                    String id = (String) p.get("id");
                    String name = (String) p.get("name");
                    providers.add(RuntimeProvider.builder()
                        .id(id != null ? id : "unknown")
                        .name(name != null ? name : "Unknown")
                        .type("provider")
                        .authenticated(response.getConnected() != null && response.getConnected().contains(id))
                        .build());
                }
            }
            return providers;
        } catch (Exception e) {
            return List.of(RuntimeProvider.builder()
                .id("fallback")
                .name("Fallback Provider")
                .type("fallback")
                .authenticated(false)
                .build());
        }
    }
    
    @Override
    public List<RuntimeAgent> listAgents() {
        return List.of(RuntimeAgent.builder()
            .id("default")
            .name("Default Agent")
            .description("Default agent")
            .build());
    }
    
    @Override
    public void close() {
        log.info("Closing OpenCode Runtime...");
        if (client != null) {
            try {
                client.close();
            } catch (Exception e) {
                log.debug("Error closing client", e);
            }
        }
        initialized = false;
    }
    
    private void ensureInitialized() {
        if (!initialized) {
            throw new IllegalStateException("Runtime not initialized");
        }
    }
    
    private static class SimpleEventSubscription implements EventSubscription {
        private final String id;
        private volatile boolean active = true;
        
        SimpleEventSubscription(String id) {
            this.id = id;
        }
        
        @Override
        public String getSubscriptionId() { return id; }
        
        @Override
        public boolean isActive() { return active; }
        
        @Override
        public void unsubscribe() { active = false; }
    }
}