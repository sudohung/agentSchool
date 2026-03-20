package ai.openclaw.ocjbot.gateway.controller;

import ai.openclaw.ocjbot.harness.Harness;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

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
}