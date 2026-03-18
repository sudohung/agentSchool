package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.provider.ProviderListResponse;
import ai.opencode.sdk.model.provider.ProviderAuthAuthorization;
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
    public ProviderListResponse list() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.get("/provider", params, ProviderListResponse.class);
    }

    /**
     * Get provider authentication methods.
     * @return map of provider ID to auth methods
     */
    public Map<String, Object> auth() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.get("/provider/auth", params, Map.class);
    }

    /**
     * Initiate OAuth authorization.
     * @param providerId provider ID
     * @param method auth method index
     * @return authorization URL and instructions
     */
    public ProviderAuthAuthorization oauthAuthorize(String providerId, Integer method) {
        Map<String, Object> body = new HashMap<>();
        if (method != null) body.put("method", method);
        return http.post("/provider/" + providerId + "/oauth/authorize", body, ProviderAuthAuthorization.class);
    }

    /**
     * Initiate OAuth authorization.
     * @param providerId provider ID
     * @return authorization URL and instructions
     */
    public ProviderAuthAuthorization oauthAuthorize(String providerId) {
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