package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.permission.PermissionRequest;
import ai.opencode.sdk.model.permission.PermissionReplyRequest;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Permission API for managing permissions.
 */
@RequiredArgsConstructor
public class PermissionAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List pending permissions.
     * @return list of permission requests
     */
    public List<PermissionRequest> list() {
        return http.get("/permission", List.class);
    }

    /**
     * Reply to a permission request.
     * @param requestId permission request ID
     * @param reply reply type (once, always, reject)
     * @param message optional message
     * @return true if successful
     */
    public Boolean reply(String requestId, String reply, String message) {
        PermissionReplyRequest request = PermissionReplyRequest.builder()
            .reply(reply)
            .message(message)
            .build();
        return http.post("/permission/" + requestId + "/reply", request, Boolean.class);
    }

    /**
     * Respond to a permission (deprecated endpoint).
     * @param sessionId session ID
     * @param permissionId permission ID
     * @param response response type
     * @return true if successful
     */
    public Boolean respond(String sessionId, String permissionId, String response) {
        Map<String, String> body = new HashMap<>();
        body.put("response", response);
        return http.post("/session/" + sessionId + "/permissions/" + permissionId, body, Boolean.class);
    }
}
