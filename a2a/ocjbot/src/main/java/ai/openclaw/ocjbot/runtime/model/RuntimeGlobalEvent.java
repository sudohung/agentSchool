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
public class RuntimeGlobalEvent {
    
    private String id;
    private String type;
    private Map<String, Object> data;
    private Instant timestamp;
}