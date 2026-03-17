package ai.opencode.sdk.model.permission;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request to reply to a permission request.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PermissionReplyRequest {
    private String reply;
    private String message;
}
