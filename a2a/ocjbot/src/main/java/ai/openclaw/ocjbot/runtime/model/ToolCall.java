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
public class ToolCall {
    
    private String id;
    private String name;
    private Map<String, Object> arguments;
    
    public static ToolCall of(String name, Map<String, Object> arguments) {
        return ToolCall.builder()
            .id(java.util.UUID.randomUUID().toString())
            .name(name)
            .arguments(arguments)
            .build();
    }
}