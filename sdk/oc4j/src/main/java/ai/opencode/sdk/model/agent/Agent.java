package ai.opencode.sdk.model.agent;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class Agent {
    private String name;
    private String description;
    private AgentMode mode;
    private Boolean native_;
    
    @JsonProperty("native")
    public void setNative(Boolean native_) {
        this.native_ = native_;
    }
    
    @JsonProperty("native")
    public Boolean getNative() {
        return native_;
    }
    
    private Boolean hidden;
    
    @JsonProperty("topP")
    private Double topP;
    
    private Double temperature;
    private String color;
    private Map<String, Object> permission;
    private Map<String, Object> model;
    private String variant;
    private String prompt;
    private Map<String, Object> options;
    private Integer steps;

    public enum AgentMode {
        @JsonProperty("subagent")
        SUBAGENT,
        @JsonProperty("primary")
        PRIMARY,
        @JsonProperty("all")
        ALL
    }
}