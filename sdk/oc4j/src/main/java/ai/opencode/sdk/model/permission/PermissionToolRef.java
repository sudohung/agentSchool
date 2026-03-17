package ai.opencode.sdk.model.permission;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

/**
 * Permission tool reference.
 */
@Data
public class PermissionToolRef {
    @JsonProperty("messageID")
    private String messageId;

    @JsonProperty("callID")
    private String callId;
}
