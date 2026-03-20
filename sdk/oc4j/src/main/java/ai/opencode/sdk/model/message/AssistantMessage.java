package ai.opencode.sdk.model.message;

import ai.opencode.sdk.model.common.TokenInfo;
import ai.opencode.sdk.model.common.PathInfo;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class AssistantMessage implements Message {
    private String id;
    
    @JsonProperty("sessionID")
    private String sessionId;
    
    private String role = "assistant";
    private TimeInfo time;
    private Map<String, Object> error;
    
    @JsonProperty("parentID")
    private String parentId;
    
    @JsonProperty("modelID")
    private String modelId;
    
    @JsonProperty("providerID")
    private String providerId;
    
    private String mode;
    private String agent;
    private PathInfo path;
    private Boolean summary;
    private double cost;
    private TokenInfo tokens;
    private Map<String, Object> structured;
    private String variant;
    private String finish;

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TimeInfo {
        private Long created;
        private Long completed;
    }
}
