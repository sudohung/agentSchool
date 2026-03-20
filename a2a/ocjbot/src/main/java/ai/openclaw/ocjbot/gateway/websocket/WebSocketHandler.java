package ai.openclaw.ocjbot.gateway.websocket;

import ai.openclaw.ocjbot.harness.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class WebSocketHandler extends TextWebSocketHandler {
    
    private static final Logger log = LoggerFactory.getLogger(WebSocketHandler.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();
    
    private static final Map<String, SessionInfo> sessions = new ConcurrentHashMap<>();
    private static final Map<String, AgentContext> agentContexts = new ConcurrentHashMap<>();
    
    private final Harness harness;
    
    public WebSocketHandler(Harness harness) {
        this.harness = harness;
    }
    
    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        log.info("WebSocket connection established: {}", session.getId());
        
        Map<String, Object> welcome = new LinkedHashMap<>();
        welcome.put("type", "welcome");
        welcome.put("message", "Welcome to OCJBot Gateway");
        welcome.put("version", "2.1.0");
        welcome.put("sessionId", session.getId());
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(welcome)));
    }
    
    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        JsonNode json = MAPPER.readTree(payload);
        
        String type = json.has("type") ? json.get("type").asText() : "unknown";
        JsonNode data = json.has("payload") ? json.get("payload") : json;
        
        log.debug("Received message type: {}", type);
        
        try {
            switch (type) {
                case "agent.send" -> handleAgentSend(session, data);
                case "session.create" -> handleSessionCreate(session, data);
                case "session.list" -> handleSessionList(session);
                case "ping" -> sendPong(session);
                case "runtime.info" -> handleRuntimeInfo(session);
                case "harness.info" -> handleHarnessInfo(session);
                default -> sendError(session, "Unknown message type: " + type);
            }
        } catch (Exception e) {
            log.error("Error handling message", e);
            sendError(session, "Error: " + e.getMessage());
        }
    }
    
    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("WebSocket transport error", exception);
    }
    
    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        log.info("WebSocket connection closed: {}, status: {}", session.getId(), status);
    }
    
    private void handleAgentSend(WebSocketSession session, JsonNode data) throws IOException {
        String message = data.has("message") ? data.get("message").asText() : "";
        String sessionId = data.has("sessionId") ? data.get("sessionId").asText() : null;
        
        if (sessionId == null || !sessions.containsKey(sessionId)) {
            sendError(session, "Session not found");
            return;
        }
        
        SessionInfo sessionInfo = sessions.get(sessionId);
        sessionInfo.messageCount++;
        sessionInfo.status = "busy";
        
        sendEvent(session, "message.received", Map.of(
            "sessionId", sessionId,
            "role", "user",
            "content", message
        ));
        
        try {
            AgentContext context = agentContexts.computeIfAbsent(sessionId, 
                id -> AgentContext.create(id, harness.getRuntime()));
            
            Goal goal = Goal.chat(message);
            
            log.info("Running AgentLoop for goal: {}", message);
            LoopResult result = harness.getAgentLoop().run(goal, context);
            
            String response = result.isSuccess() ? result.getOutput() : "Error: " + result.getError();
            
            sessionInfo.status = "idle";
            
            ObjectNode responseNode = MAPPER.createObjectNode();
            responseNode.put("type", "agent.response");
            responseNode.put("sessionId", sessionId);
            responseNode.put("message", response);
            responseNode.put("iterations", result.getIterations());
            responseNode.put("status", result.getStatus().name());
            
            session.sendMessage(new TextMessage(MAPPER.writeValueAsString(responseNode)));
            
            sendEvent(session, "message.sent", Map.of(
                "sessionId", sessionId,
                "role", "assistant",
                "content", response
            ));
            
        } catch (Exception e) {
            log.error("Agent execution failed", e);
            sessionInfo.status = "error";
            sendError(session, "Agent execution failed: " + e.getMessage());
        }
    }
    
    private void handleSessionCreate(WebSocketSession session, JsonNode data) throws IOException {
        String sessionId = UUID.randomUUID().toString();
        String title = data.has("title") ? data.get("title").asText() : "New Session";
        
        SessionInfo info = new SessionInfo();
        info.id = sessionId;
        info.title = title;
        info.status = "idle";
        info.createdAt = System.currentTimeMillis();
        
        sessions.put(sessionId, info);
        
        AgentContext context = AgentContext.create(sessionId, harness.getRuntime());
        agentContexts.put(sessionId, context);
        
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "session.created");
        response.put("sessionId", sessionId);
        response.put("title", title);
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(response)));
        
        log.info("Session created: {}", sessionId);
    }
    
    private void handleSessionList(WebSocketSession session) throws IOException {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "session.list");
        
        List<Map<String, Object>> sessionList = new ArrayList<>();
        for (SessionInfo info : sessions.values()) {
            Map<String, Object> s = new LinkedHashMap<>();
            s.put("id", info.id);
            s.put("title", info.title);
            s.put("status", info.status);
            s.put("messageCount", info.messageCount);
            sessionList.add(s);
        }
        response.put("sessions", MAPPER.valueToTree(sessionList));
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(response)));
    }
    
    private void handleRuntimeInfo(WebSocketSession session) throws IOException {
        var runtime = harness.getRuntime();
        var health = runtime.checkHealth();
        
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "runtime.info");
        response.put("name", runtime.getName());
        response.put("type", runtime.getType().getCode());
        response.put("healthy", health.isHealthy());
        response.put("status", health.getStatus());
        response.put("activeSessions", sessions.size());
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(response)));
    }
    
    private void handleHarnessInfo(WebSocketSession session) throws IOException {
        var agentLoop = harness.getAgentLoop();
        
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "harness.info");
        response.put("agentLoop", agentLoop.getName());
        response.put("maxIterations", agentLoop.getMaxIterations());
        response.put("activeSessions", sessions.size());
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(response)));
    }
    
    private void sendEvent(WebSocketSession session, String eventType, Map<String, Object> data) throws IOException {
        ObjectNode event = MAPPER.createObjectNode();
        event.put("type", "event");
        event.put("eventType", eventType);
        event.put("timestamp", System.currentTimeMillis());
        event.set("data", MAPPER.valueToTree(data));
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(event)));
    }
    
    private void sendPong(WebSocketSession session) throws IOException {
        ObjectNode pong = MAPPER.createObjectNode();
        pong.put("type", "pong");
        pong.put("timestamp", System.currentTimeMillis());
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(pong)));
    }
    
    private void sendError(WebSocketSession session, String error) throws IOException {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "error");
        response.put("message", error);
        response.put("timestamp", System.currentTimeMillis());
        
        session.sendMessage(new TextMessage(MAPPER.writeValueAsString(response)));
    }
    
    private static class SessionInfo {
        String id;
        String title;
        String status;
        long createdAt;
        int messageCount;
    }
}