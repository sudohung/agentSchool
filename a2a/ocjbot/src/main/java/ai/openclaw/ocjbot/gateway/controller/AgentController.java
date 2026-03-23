package ai.openclaw.ocjbot.gateway.controller;

import ai.openclaw.ocjbot.harness.Harness;
import ai.openclaw.ocjbot.runtime.model.RuntimeMessage;
import ai.openclaw.ocjbot.runtime.model.RuntimeSession;
import ai.openclaw.ocjbot.runtime.model.SessionCreateRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class AgentController {

    private final Harness harness;

    public AgentController(Harness harness) {
        this.harness = harness;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        var health = harness.getRuntime().checkHealth();
        return ResponseEntity.ok(Map.of(
            "status", health.isHealthy() ? "UP" : "DOWN",
            "healthy", health.isHealthy(),
            "runtime", harness.getRuntime().getName(),
            "version", "2.1.0"
        ));
    }

    @GetMapping("/runtime/info")
    public ResponseEntity<Map<String, Object>> runtimeInfo() {
        var runtime = harness.getRuntime();
        var health = runtime.checkHealth();
        
        return ResponseEntity.ok(Map.of(
            "name", runtime.getName(),
            "type", runtime.getType().getCode(),
            "healthy", health.isHealthy(),
            "status", health.getStatus()
        ));
    }

    @GetMapping("/harness/info")
    public ResponseEntity<Map<String, Object>> harnessInfo() {
        return ResponseEntity.ok(Map.of(
            "agentLoop", harness.getAgentLoop().getName(),
            "maxIterations", harness.getAgentLoop().getMaxIterations()
        ));
    }

    @GetMapping("/agent/info")
    public ResponseEntity<Map<String, Object>> agentInfo() {
        var props = harness.getProperties();
        return ResponseEntity.ok(Map.of(
            "name", props.getAgent().getName(),
            "model", props.getAgent().getModel(),
            "description", props.getAgent().getDescription()
        ));
    }

    @GetMapping("/sessions")
    public ResponseEntity<List<Map<String, Object>>> listSessions() {
        var sessions = harness.getRuntime().listSessions();
        var result = sessions.stream().map(this::toSessionMap).toList();
        return ResponseEntity.ok(result);
    }

    @PostMapping("/sessions")
    public ResponseEntity<Map<String, Object>> createSession(@RequestBody(required = false) Map<String, String> body) {
        var request = new SessionCreateRequest();
        if (body != null && body.containsKey("title")) {
            request.setTitle(body.get("title"));
        }
        var session = harness.getRuntime().createSession(request);
        return ResponseEntity.ok(toSessionMap(session));
    }

    @GetMapping("/sessions/{id}")
    public ResponseEntity<Map<String, Object>> getSession(@PathVariable String id) {
        var session = harness.getRuntime().getSession(id);
        if (session == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(toSessionMap(session));
    }

    @DeleteMapping("/sessions/{id}")
    public ResponseEntity<Void> deleteSession(@PathVariable String id) {
        harness.getRuntime().deleteSession(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/sessions/{id}/messages")
    public ResponseEntity<List<Map<String, Object>>> listMessages(@PathVariable String id) {
        var messages = harness.getRuntime().listMessages(id);
        var result = messages.stream().map(this::toMessageMap).toList();
        return ResponseEntity.ok(result);
    }

    private Map<String, Object> toSessionMap(RuntimeSession session) {
        return Map.of(
            "id", session.getId(),
            "title", session.getTitle() != null ? session.getTitle() : "Untitled Session",
            "state", session.getState() != null ? session.getState().name().toLowerCase() : "idle",
            "createdAt", session.getCreatedAt() != null ? session.getCreatedAt().toString() : "",
            "updatedAt", session.getUpdatedAt() != null ? session.getUpdatedAt().toString() : ""
        );
    }

    private Map<String, Object> toMessageMap(RuntimeMessage message) {
        String content = message.getParts().stream()
            .filter(p -> p.getText() != null)
            .map(p -> p.getText())
            .reduce("", String::concat);
        
        return Map.of(
            "id", message.getId(),
            "role", message.getRole().name().toLowerCase(),
            "content", content,
            "timestamp", message.getTimestamp() != null ? message.getTimestamp().toString() : ""
        );
    }
}