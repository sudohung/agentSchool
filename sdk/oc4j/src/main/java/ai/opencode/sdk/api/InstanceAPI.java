package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

/**
 * Instance API for instance management.
 */
@RequiredArgsConstructor
public class InstanceAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Dispose the current instance.
     * Clean up and dispose the current OpenCode instance,
     * releasing all resources.
     * @return true if disposed successfully
     */
    public Boolean dispose() {
        return http.post("/instance/dispose", null, Boolean.class);
    }
}