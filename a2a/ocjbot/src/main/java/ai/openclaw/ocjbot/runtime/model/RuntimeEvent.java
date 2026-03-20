package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuntimeEvent {
    
    private String id;
    private String sessionId;
    private String type;
    private Map<String, Object> data;
    private Instant timestamp;
    
    public static RuntimeEvent of(String sessionId, String type, Map<String, Object> data) {
        return RuntimeEvent.builder()
            .id(java.util.UUID.randomUUID().toString())
            .sessionId(sessionId)
            .type(type)
            .data(data)
            .timestamp(Instant.now())
            .build();
    }
    
    public boolean isMessageEvent() {
        return type != null && type.startsWith("message.");
    }
    
    public boolean isToolEvent() {
        return type != null && type.startsWith("tool.");
    }
    
    public boolean isErrorEvent() {
        return "error".equals(type);
    }
}