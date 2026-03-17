package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.Map;

/**
 * VCS (Version Control System) API.
 */
@RequiredArgsConstructor
public class VcsAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Get VCS information.
     * @return VCS info including current branch
     */
    public Map<String, Object> get() {
        return http.get("/vcs", Map.class);
    }
}