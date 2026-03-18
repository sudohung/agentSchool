package ai.opencode.sdk.model.event;

import ai.opencode.sdk.model.permission.PermissionRequest;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@JsonIgnoreProperties(ignoreUnknown = true)
public class EventPermissionAsked extends Event {
    private PermissionRequest properties;
}