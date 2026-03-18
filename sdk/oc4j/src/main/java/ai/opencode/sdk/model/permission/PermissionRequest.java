package ai.opencode.sdk.model.permission;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;
import java.util.Map;

/**
 * Permission request from AI assistant.
 */
@Data
public class PermissionRequest {
    private String id;

    @JsonProperty("sessionID")
    private String sessionId;

    @JsonProperty("requestID")
    private String requestId;

    private String permission;
    private List<String> patterns;
    private Map<String, Object> metadata;
    private List<String> always;
    private PermissionToolRef tool;
}
