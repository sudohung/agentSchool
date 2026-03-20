package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ToolCallRequest {
    
    private String toolName;
    private Map<String, Object> arguments;
    private int timeout;
    
    public static ToolCallRequest of(String toolName, Map<String, Object> arguments) {
        return ToolCallRequest.builder()
            .toolName(toolName)
            .arguments(arguments)
            .timeout(30000)
            .build();
    }
}