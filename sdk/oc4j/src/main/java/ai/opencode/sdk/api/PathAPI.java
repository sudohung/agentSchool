package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.Map;

/**
 * Path API for path information.
 */
@RequiredArgsConstructor
public class PathAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Get path information.
     * @return path info including home, state, config, worktree
     */
    public Map<String, Object> get() {
        return http.get("/path", Map.class);
    }
}