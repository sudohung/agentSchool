package ai.openclaw.ocjbot.gateway;

import ai.openclaw.ocjbot.harness.*;
import ai.openclaw.ocjbot.harness.loop.ReActLoop;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.http.websocketx.TextWebSocketFrame;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class WebSocketHandler extends SimpleChannelInboundHandler<TextWebSocketFrame> {
    private static final Logger log = LoggerFactory.getLogger(WebSocketHandler.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();
    
    private static final Map<String, SessionInfo> sessions = new ConcurrentHashMap<>();
    private static final Map<String, AgentContext> agentContexts = new ConcurrentHashMap<>();
    
    private final Harness harness;
    private String sessionId;
    
    public WebSocketHandler(Harness harness) {
        this.harness = harness;
    }
    
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, TextWebSocketFrame frame) throws Exception {
        String text = frame.text();
        JsonNode message = MAPPER.readTree(text);
        
        String type = message.has("type") ? message.get("type").asText() : "unknown";
        JsonNode payload = message.has("payload") ? message.get("payload") : message;
        
        log.debug("Received message type: {}", type);
        
        switch (type) {
            case "agent.send" -> handleAgentSend(ctx, payload);
            case "session.create" -> handleSessionCreate(ctx, payload);
            case "session.list" -> handleSessionList(ctx);
            case "session.select" -> handleSessionSelect(ctx, payload);
            case "ping" -> sendPong(ctx);
            case "runtime.info" -> handleRuntimeInfo(ctx);
            case "harness.info" -> handleHarnessInfo(ctx);
            default -> sendError(ctx, "Unknown message type: " + type);
        }
    }
    
    private void handleAgentSend(ChannelHandlerContext ctx, JsonNode payload) {
        String userMessage = payload.has("message") ? payload.get("message").asText() : "";
        String targetSession = payload.has("sessionId") ? payload.get("sessionId").asText() : sessionId;
        
        if (targetSession == null) {
            sendError(ctx, "No session selected");
            return;
        }
        
        SessionInfo sessionInfo = sessions.get(targetSession);
        if (sessionInfo == null) {
            sendError(ctx, "Session not found: " + targetSession);
            return;
        }
        
        sendEvent(ctx, "message.received", Map.of(
            "sessionId", targetSession,
            "role", "user",
            "content", userMessage
        ));
        
        sessionInfo.messageCount++;
        sessionInfo.status = "busy";
        
        try {
            AgentContext agentContext = agentContexts.computeIfAbsent(targetSession, 
                id -> AgentContext.create(id, harness.getRuntime()));
            
            Goal goal = Goal.chat(userMessage);
            
            log.info("Running AgentLoop for goal: {}", userMessage);
            LoopResult result = harness.getAgentLoop().run(goal, agentContext);
            
            String aiResponse;
            if (result.isSuccess()) {
                aiResponse = result.getOutput();
            } else {
                aiResponse = "Error: " + result.getError();
            }
            
            sessionInfo.status = "idle";
            
            ObjectNode response = MAPPER.createObjectNode();
            response.put("type", "agent.response");
            response.put("sessionId", targetSession);
            response.put("message", aiResponse);
            response.put("iterations", result.getIterations());
            response.put("status", result.getStatus().name());
            
            ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
            
            sendEvent(ctx, "message.sent", Map.of(
                "sessionId", targetSession,
                "role", "assistant",
                "content", aiResponse,
                "iterations", result.getIterations()
            ));
            
        } catch (Exception e) {
            log.error("Agent execution failed", e);
            sessionInfo.status = "error";
            sendError(ctx, "Agent execution failed: " + e.getMessage());
        }
    }
    
    private void handleSessionCreate(ChannelHandlerContext ctx, JsonNode payload) {
        String newSessionId = UUID.randomUUID().toString();
        String title = payload.has("title") ? payload.get("title").asText() : "New Session";
        
        SessionInfo info = new SessionInfo();
        info.id = newSessionId;
        info.title = title;
        info.status = "idle";
        info.createdAt = System.currentTimeMillis();
        
        sessions.put(newSessionId, info);
        
        AgentContext agentContext = AgentContext.create(newSessionId, harness.getRuntime());
        agentContexts.put(newSessionId, agentContext);
        
        this.sessionId = newSessionId;
        
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "session.created");
        response.put("sessionId", newSessionId);
        response.put("title", title);
        
        ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
        
        sendEvent(ctx, "session.new", Map.of(
            "sessionId", newSessionId,
            "title", title
        ));
        
        log.info("Session created: {}", newSessionId);
    }
    
    private void handleSessionList(ChannelHandlerContext ctx) {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "session.list");
        
        ObjectNode sessionsArray = MAPPER.createArrayNode();
        for (SessionInfo info : sessions.values()) {
            ObjectNode sessionNode = MAPPER.createObjectNode();
            sessionNode.put("id", info.id);
            sessionNode.put("title", info.title);
            sessionNode.put("status", info.status);
            sessionNode.put("messageCount", info.messageCount);
            sessionsArray.add(sessionNode);
        }
        response.set("sessions", sessionsArray);
        
        ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
    }
    
    private void handleSessionSelect(ChannelHandlerContext ctx, JsonNode payload) {
        String targetId = payload.has("sessionId") ? payload.get("sessionId").asText() : null;
        
        if (targetId != null && sessions.containsKey(targetId)) {
            this.sessionId = targetId;
            
            ObjectNode response = MAPPER.createObjectNode();
            response.put("type", "session.selected");
            response.put("sessionId", targetId);
            
            ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
        } else {
            sendError(ctx, "Session not found: " + targetId);
        }
    }
    
    private void handleRuntimeInfo(ChannelHandlerContext ctx) {
        var runtime = harness.getRuntime();
        var health = runtime.checkHealth();
        
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "runtime.info");
        response.put("name", runtime.getName());
        response.put("type", runtime.getType().getCode());
        response.put("healthy", health.isHealthy());
        response.put("status", health.getStatus());
        response.put("activeSessions", sessions.size());
        
        ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
    }
    
    private void handleHarnessInfo(ChannelHandlerContext ctx) {
        var agentLoop = harness.getAgentLoop();
        
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "harness.info");
        response.put("agentLoop", agentLoop.getName());
        response.put("maxIterations", agentLoop.getMaxIterations());
        response.put("activeSessions", sessions.size());
        
        ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
    }
    
    private void sendEvent(ChannelHandlerContext ctx, String eventType, Map<String, Object> data) {
        ObjectNode event = MAPPER.createObjectNode();
        event.put("type", "event");
        event.put("eventType", eventType);
        event.put("timestamp", System.currentTimeMillis());
        
        ObjectNode eventData = MAPPER.valueToTree(data);
        event.set("data", eventData);
        
        ctx.writeAndFlush(new TextWebSocketFrame(event.toString()));
    }
    
    private void sendPong(ChannelHandlerContext ctx) {
        ObjectNode pong = MAPPER.createObjectNode();
        pong.put("type", "pong");
        pong.put("timestamp", System.currentTimeMillis());
        
        ctx.writeAndFlush(new TextWebSocketFrame(pong.toString()));
    }
    
    private void sendError(ChannelHandlerContext ctx, String error) {
        ObjectNode response = MAPPER.createObjectNode();
        response.put("type", "error");
        response.put("message", error);
        response.put("timestamp", System.currentTimeMillis());
        
        ctx.writeAndFlush(new TextWebSocketFrame(response.toString()));
    }
    
    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        log.error("WebSocket error", cause);
        ctx.close();
    }
    
    private static class SessionInfo {
        String id;
        String title;
        String status;
        long createdAt;
        int messageCount;
    }
}