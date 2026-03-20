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
public class PermissionRequest {
    
    private String id;
    private String sessionId;
    private String permission;
    private String message;
    private Map<String, Object> context;
    private Instant createdAt;
}