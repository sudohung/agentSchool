package ai.opencode.sdk.model.message;

import ai.opencode.sdk.model.common.TimeInfo;
import ai.opencode.sdk.model.common.ModelRef;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.Map;

/**
 * User message.
 */
@Data
public class UserMessage {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private String role = "user";
    private TimeInfo time;
    private Map<String, Object> format;
    private Map<String, Object> summary;
    private String agent;
    private ModelRef model;
    private String system;
    private Map<String, Boolean> tools;
    private String variant;
}
