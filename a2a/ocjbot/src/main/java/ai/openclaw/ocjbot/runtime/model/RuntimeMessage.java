package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuntimeMessage {
    
    private String id;
    private String sessionId;
    private MessageRole role;
    private List<MessagePart> parts;
    private Instant timestamp;
    private Map<String, Object> metadata;
    
    public enum MessageRole {
        USER,
        ASSISTANT,
        SYSTEM,
        TOOL
    }
    
    public String getTextContent() {
        if (parts == null) return null;
        return parts.stream()
            .filter(p -> "text".equals(p.getType()))
            .map(MessagePart::getText)
            .reduce("", (a, b) -> a + b);
    }
    
    public boolean hasToolCalls() {
        if (parts == null) return false;
        return parts.stream().anyMatch(p -> "tool_call".equals(p.getType()));
    }
    
    public List<ToolCall> getToolCalls() {
        if (parts == null) return List.of();
        return parts.stream()
            .filter(p -> "tool_call".equals(p.getType()))
            .map(MessagePart::getToolCall)
            .toList();
    }
}