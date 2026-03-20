package ai.openclaw.ocjbot.harness;

import ai.openclaw.ocjbot.runtime.AgentRuntime;
import ai.openclaw.ocjbot.runtime.model.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Agent 上下文
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AgentContext {
    
    private String sessionId;
    private String userId;
    private AgentRuntime runtime;
    private List<RuntimeMessage> messages;
    private Map<String, Object> state;
    private int iterationCount;
    private int maxIterations;
    private Instant startTime;
    
    public void addMessage(RuntimeMessage message) {
        if (messages == null) {
            messages = new ArrayList<>();
        }
        messages.add(message);
    }
    
    public void incrementIteration() {
        iterationCount++;
    }
    
    public boolean hasExceededMaxIterations() {
        return iterationCount >= maxIterations;
    }
    
    public static AgentContext create(String sessionId, AgentRuntime runtime) {
        return AgentContext.builder()
            .sessionId(sessionId)
            .runtime(runtime)
            .messages(new ArrayList<>())
            .state(new HashMap<>())
            .iterationCount(0)
            .maxIterations(10)
            .startTime(Instant.now())
            .build();
    }
}