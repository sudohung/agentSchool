package ai.openclaw.ocjbot.runtime.mock;

import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.RuntimeType;
import ai.openclaw.ocjbot.runtime.model.*;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

public class MockRuntime implements AgentRuntime {
    
    private final Map<String, RuntimeSession> sessions = new ConcurrentHashMap<>();
    private final Map<String, List<RuntimeMessage>> messages = new ConcurrentHashMap<>();
    private final AtomicInteger messageIdCounter = new AtomicInteger(0);
    private volatile boolean initialized = false;
    
    @Override
    public void initialize() {
        initialized = true;
    }
    
    @Override
    public RuntimeHealth checkHealth() {
        return RuntimeHealth.healthy();
    }
    
    @Override
    public String getName() {
        return "Mock Runtime";
    }
    
    @Override
    public RuntimeType getType() {
        return RuntimeType.MOCK;
    }
    
    @Override
    public RuntimeSession createSession(SessionCreateRequest request) {
        String id = UUID.randomUUID().toString();
        RuntimeSession session = RuntimeSession.builder()
            .id(id)
            .title(request.getTitle() != null ? request.getTitle() : "Mock Session")
            .state(RuntimeSession.SessionState.IDLE)
            .createdAt(Instant.now())
            .build();
        sessions.put(id, session);
        messages.put(id, new ArrayList<>());
        return session;
    }
    
    @Override
    public RuntimeSession getSession(String sessionId) {
        return sessions.get(sessionId);
    }
    
    @Override
    public List<RuntimeSession> listSessions() {
        return new ArrayList<>(sessions.values());
    }
    
    @Override
    public boolean deleteSession(String sessionId) {
        sessions.remove(sessionId);
        messages.remove(sessionId);
        return true;
    }
    
    @Override
    public SessionStatus getSessionStatus(String sessionId) {
        RuntimeSession session = sessions.get(sessionId);
        if (session == null) {
            return SessionStatus.builder().sessionId(sessionId).status("not_found").build();
        }
        return SessionStatus.builder()
            .sessionId(sessionId)
            .status(session.getState().name().toLowerCase())
            .build();
    }
    
    @Override
    public RuntimeMessage sendMessage(String sessionId, MessageRequest request) {
        return sendText(sessionId, request.getText());
    }
    
    @Override
    public RuntimeMessage sendText(String sessionId, String text) {
        List<RuntimeMessage> sessionMessages = messages.computeIfAbsent(sessionId, k -> new ArrayList<>());
        
        RuntimeMessage userMsg = RuntimeMessage.builder()
            .id("msg-" + messageIdCounter.incrementAndGet())
            .sessionId(sessionId)
            .role(RuntimeMessage.MessageRole.USER)
            .parts(List.of(MessagePart.text(text)))
            .timestamp(Instant.now())
            .build();
        sessionMessages.add(userMsg);
        
        RuntimeMessage assistantMsg = RuntimeMessage.builder()
            .id("msg-" + messageIdCounter.incrementAndGet())
            .sessionId(sessionId)
            .role(RuntimeMessage.MessageRole.ASSISTANT)
            .parts(List.of(MessagePart.text("Mock response: " + text)))
            .timestamp(Instant.now())
            .build();
        sessionMessages.add(assistantMsg);
        
        return assistantMsg;
    }
    
    @Override
    public void sendMessageStream(String sessionId, MessageRequest request, Consumer<RuntimeEvent> eventHandler) {
        eventHandler.accept(RuntimeEvent.of(sessionId, "message.start", Map.of()));
        RuntimeMessage response = sendMessage(sessionId, request);
        eventHandler.accept(RuntimeEvent.of(sessionId, "message.complete", 
            Map.of("messageId", response.getId())));
    }
    
    @Override
    public List<RuntimeMessage> listMessages(String sessionId) {
        return messages.getOrDefault(sessionId, List.of());
    }
    
    @Override
    public RuntimeMessage getMessage(String sessionId, String messageId) {
        List<RuntimeMessage> sessionMessages = messages.get(sessionId);
        if (sessionMessages == null) return null;
        return sessionMessages.stream()
            .filter(m -> messageId.equals(m.getId()))
            .findFirst()
            .orElse(null);
    }
    
    @Override
    public ToolResult executeTool(String sessionId, ToolCallRequest request) {
        return ToolResult.success("Mock tool result for: " + request.getToolName());
    }
    
    @Override
    public RuntimeMessage executeShell(String sessionId, String command) {
        return RuntimeMessage.builder()
            .id("msg-" + messageIdCounter.incrementAndGet())
            .sessionId(sessionId)
            .role(RuntimeMessage.MessageRole.ASSISTANT)
            .parts(List.of(MessagePart.text("Mock shell result: " + command)))
            .timestamp(Instant.now())
            .build();
    }
    
    @Override
    public EventSubscription subscribeEvents(Consumer<RuntimeEvent> eventHandler) {
        return new MockEventSubscription(UUID.randomUUID().toString());
    }
    
    @Override
    public EventSubscription subscribeGlobalEvents(Consumer<RuntimeGlobalEvent> eventHandler) {
        return new MockEventSubscription(UUID.randomUUID().toString());
    }
    
    @Override
    public List<PermissionRequest> listPendingPermissions() {
        return List.of();
    }
    
    @Override
    public boolean replyPermission(String permissionId, PermissionReply reply) {
        return true;
    }
    
    @Override
    public List<RuntimeProvider> listProviders() {
        return List.of(
            RuntimeProvider.builder()
                .id("mock-provider")
                .name("Mock Provider")
                .type("mock")
                .authenticated(true)
                .build()
        );
    }
    
    @Override
    public List<RuntimeAgent> listAgents() {
        return List.of(
            RuntimeAgent.builder()
                .id("mock-agent")
                .name("Mock Agent")
                .description("A mock agent for testing")
                .build()
        );
    }
    
    @Override
    public void close() {
        sessions.clear();
        messages.clear();
        initialized = false;
    }
    
    private static class MockEventSubscription implements EventSubscription {
        private final String id;
        private volatile boolean active = true;
        
        MockEventSubscription(String id) {
            this.id = id;
        }
        
        @Override
        public String getSubscriptionId() {
            return id;
        }
        
        @Override
        public boolean isActive() {
            return active;
        }
        
        @Override
        public void unsubscribe() {
            active = false;
        }
    }
}