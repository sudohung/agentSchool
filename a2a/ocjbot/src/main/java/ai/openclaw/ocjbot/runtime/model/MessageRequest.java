package ai.openclaw.ocjbot.runtime.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MessageRequest {
    
    private String text;
    private List<Map<String, Object>> parts;
    private String providerId;
    private String modelId;
    private String agent;
    private String systemPrompt;
    private boolean stream;
    private Map<String, Object> format;
    
    public static MessageRequest text(String text) {
        return MessageRequest.builder()
            .text(text)
            .build();
    }
    
    public static MessageRequest of(String text, String providerId, String modelId) {
        return MessageRequest.builder()
            .text(text)
            .providerId(providerId)
            .modelId(modelId)
            .build();
    }
    
    public static MessageRequest plan(String text, String agent) {
        return MessageRequest.builder()
            .text(text)
            .agent(agent)
            .build();
    }
    
    public static MessageRequest withProvider(String text, String providerId, String modelId) {
        return MessageRequest.builder()
            .text(text)
            .providerId(providerId)
            .modelId(modelId)
            .build();
    }
    
    public static MessageRequest withAgentAndProvider(String text, String agent, String providerId, String modelId) {
        return MessageRequest.builder()
            .text(text)
            .agent(agent)
            .providerId(providerId)
            .modelId(modelId)
            .build();
    }
}