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
public class RuntimeSession {
    
    private String id;
    private String title;
    private String parentId;
    private String workspaceId;
    private SessionState state;
    private List<Map<String, Object>> permissions;
    private Instant createdAt;
    private Instant updatedAt;
    private Map<String, Object> metadata;
    
    public enum SessionState {
        IDLE,
        BUSY,
        RETRY,
        ERROR
    }
    
    public boolean isIdle() {
        return state == SessionState.IDLE;
    }
    
    public boolean isBusy() {
        return state == SessionState.BUSY;
    }
}