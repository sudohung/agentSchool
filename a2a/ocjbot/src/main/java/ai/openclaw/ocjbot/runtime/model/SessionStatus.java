package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SessionStatus {
    
    private String sessionId;
    private String status;
    private String message;
    private int retryCount;
    private boolean aborted;
    
    public boolean isBusy() {
        return "busy".equalsIgnoreCase(status);
    }
    
    public boolean isIdle() {
        return "idle".equalsIgnoreCase(status);
    }
    
    public boolean isRetry() {
        return "retry".equalsIgnoreCase(status);
    }
}