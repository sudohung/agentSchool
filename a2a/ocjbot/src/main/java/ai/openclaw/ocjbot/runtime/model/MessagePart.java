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
public class MessagePart {
    
    private String id;
    private String type;
    private String text;
    private ToolCall toolCall;
    private Map<String, Object> content;
    
    public static MessagePart text(String text) {
        return MessagePart.builder()
            .type("text")
            .text(text)
            .build();
    }
    
    public static MessagePart toolCall(ToolCall toolCall) {
        return MessagePart.builder()
            .type("tool_call")
            .toolCall(toolCall)
            .build();
    }
    
    public static MessagePart toolResult(String toolCallId, String result) {
        return MessagePart.builder()
            .type("tool_result")
            .content(Map.of(
                "tool_call_id", toolCallId,
                "result", result
            ))
            .build();
    }
}