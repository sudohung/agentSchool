package ai.opencode.sdk.model.permission;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class PermissionRule {
    private String permission;
    private String pattern;
    private PermissionAction action;

    public enum PermissionAction {
        @JsonProperty("allow")
        ALLOW,
        @JsonProperty("deny")
        DENY,
        @JsonProperty("ask")
        ASK
    }
}