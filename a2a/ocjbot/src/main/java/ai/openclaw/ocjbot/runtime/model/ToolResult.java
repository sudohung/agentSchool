package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ToolResult {
    
    private boolean success;
    private String output;
    private String error;
    private int exitCode;
    
    public static ToolResult success(String output) {
        return ToolResult.builder()
            .success(true)
            .output(output)
            .build();
    }
    
    public static ToolResult failure(String error) {
        return ToolResult.builder()
            .success(false)
            .error(error)
            .build();
    }
    
    public static ToolResult of(int exitCode, String output, String error) {
        return ToolResult.builder()
            .success(exitCode == 0)
            .exitCode(exitCode)
            .output(output)
            .error(error)
            .build();
    }
}