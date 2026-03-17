package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.Map;

/**
 * Config API for managing configuration.
 */
@RequiredArgsConstructor
public class ConfigAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Get configuration.
     * @return configuration
     */
    public Map<String, Object> get() {
        return http.get("/config", Map.class);
    }

    /**
     * Update configuration.
     * @param config configuration updates
     * @return updated configuration
     */
    public Map<String, Object> update(Map<String, Object> config) {
        return http.patch("/config", config, Map.class);
    }

    /**
     * Get configured providers.
     * @return providers and default models
     */
    public Map<String, Object> providers() {
        return http.get("/config/providers", Map.class);
    }
}