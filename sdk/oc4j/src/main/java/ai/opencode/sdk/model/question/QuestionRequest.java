package ai.opencode.sdk.model.question;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class QuestionRequest {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private List<QuestionInfo> questions;
    
    private ToolRef tool;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ToolRef {
        @JsonProperty("messageID")
        private String messageId;
        
        @JsonProperty("callID")
        private String callId;
    }
}