package ai.openclaw.ocjbot.tool;

import com.fasterxml.jackson.databind.JsonNode;

public interface Tool {
    
    String getName();
    
    String getDescription();
    
    String getParametersSchema();
    
    ToolResult execute(ToolContext context, JsonNode parameters);
}