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
}
