package ai.opencode.sdk.model.agent;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class AgentPermission {
    private String permission;
    private PermissionAction action;
    private String pattern;

    public enum PermissionAction {
        @JsonProperty("allow")
        ALLOW,
        @JsonProperty("deny")
        DENY,
        @JsonProperty("ask")
        ASK
    }
}