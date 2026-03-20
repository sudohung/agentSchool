package ai.openclaw.ocjbot.harness;

import ai.openclaw.ocjbot.runtime.model.RuntimeMessage;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Agent 目标
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Goal {
    
    private String id;
    private String description;
    private GoalType type;
    private Map<String, Object> parameters;
    
    public enum GoalType {
        CHAT,
        TASK,
        QUESTION,
        ACTION
    }
    
    public static Goal chat(String message) {
        return Goal.builder()
            .id(java.util.UUID.randomUUID().toString())
            .description(message)
            .type(GoalType.CHAT)
            .parameters(new HashMap<>())
            .build();
    }
    
    public static Goal task(String description) {
        return Goal.builder()
            .id(java.util.UUID.randomUUID().toString())
            .description(description)
            .type(GoalType.TASK)
            .parameters(new HashMap<>())
            .build();
    }
    
    public boolean isAchieved() {
        return false;
    }
}