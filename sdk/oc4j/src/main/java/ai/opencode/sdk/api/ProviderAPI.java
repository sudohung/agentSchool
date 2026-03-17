package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.Map;

/**
 * Provider API for managing providers.
 */
@RequiredArgsConstructor
public class ProviderAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List providers.
     * @return providers
     */
    public Map<String, Object> list() {
        return http.get("/provider", Map.class);
    }

    /**
     * Get provider auth info.
     * @return auth info
     */
    public Map<String, Object> auth() {
        return http.get("/provider/auth", Map.class);
    }
}
