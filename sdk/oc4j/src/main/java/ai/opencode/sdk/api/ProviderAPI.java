package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.Map;

/**
 * Provider API for managing AI providers.
 */
@RequiredArgsConstructor
public class ProviderAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List all providers.
     * @return list of providers with default models and connected providers
     */
    public Map<String, Object> list() {
        return http.get("/provider", Map.class);
    }

    /**
     * Get provider authentication methods.
     * @return map of provider ID to auth methods
     */
    public Map<String, Object> auth() {
        return http.get("/provider/auth", Map.class);
    }

    /**
     * Initiate OAuth authorization.
     * @param providerId provider ID
     * @param method auth method index
     * @return authorization URL and instructions
     */
    public Map<String, Object> oauthAuthorize(String providerId, Integer method) {
        Map<String, Object> body = new HashMap<>();
        if (method != null) body.put("method", method);
        return http.post("/provider/" + providerId + "/oauth/authorize", body, Map.class);
    }

    /**
     * Initiate OAuth authorization.
     * @param providerId provider ID
     * @return authorization URL and instructions
     */
    public Map<String, Object> oauthAuthorize(String providerId) {
        return oauthAuthorize(providerId, null);
    }

    /**
     * Handle OAuth callback.
     * @param providerId provider ID
     * @param method auth method index
     * @param code OAuth authorization code
     * @return true if successful
     */
    public Boolean oauthCallback(String providerId, Integer method, String code) {
        Map<String, Object> body = new HashMap<>();
        if (method != null) body.put("method", method);
        if (code != null) body.put("code", code);
        return http.post("/provider/" + providerId + "/oauth/callback", body, Boolean.class);
    }
}