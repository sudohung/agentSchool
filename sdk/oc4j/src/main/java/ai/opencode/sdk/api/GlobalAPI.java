package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.Map;

/**
 * Global API for global operations.
 */
@RequiredArgsConstructor
public class GlobalAPI {
    private final HttpClient http;

    /**
     * Get health status.
     * @return health info
     */
    public Map<String, Object> health() {
        return http.get("/global/health", Map.class);
    }

    /**
     * Get global configuration.
     * @return global config
     */
    public Map<String, Object> config() {
        return http.get("/global/config", Map.class);
    }

    /**
     * Update global configuration.
     * @param config new configuration
     * @return updated config
     */
    public Map<String, Object> updateConfig(Map<String, Object> config) {
        return http.patch("/global/config", config, Map.class);
    }

    /**
     * Dispose instance.
     * @return true if successful
     */
    public Boolean dispose() {
        return http.post("/global/dispose", null, Boolean.class);
    }
}
