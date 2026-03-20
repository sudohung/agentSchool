package ai.openclaw.ocjbot.tool;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.TextNode;

public record ToolResult(
    boolean success,
    JsonNode output,
    String error
) {
    public static ToolResult success(String output) {
        return new ToolResult(true, TextNode.valueOf(output), null);
    }
    
    public static ToolResult success(JsonNode output) {
        return new ToolResult(true, output, null);
    }
    
    public static ToolResult failure(String error) {
        return new ToolResult(false, null, error);
    }
}