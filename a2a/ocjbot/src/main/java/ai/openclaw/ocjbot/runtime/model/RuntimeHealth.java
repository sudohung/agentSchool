package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuntimeHealth {
    
    private boolean healthy;
    private String status;
    private String version;
    private String message;
    
    public static RuntimeHealth healthy() {
        return RuntimeHealth.builder()
            .healthy(true)
            .status("UP")
            .build();
    }
    
    public static RuntimeHealth unhealthy(String message) {
        return RuntimeHealth.builder()
            .healthy(false)
            .status("DOWN")
            .message(message)
            .build();
    }
}