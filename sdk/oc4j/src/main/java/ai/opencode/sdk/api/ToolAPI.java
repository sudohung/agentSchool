package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Tool API for tool management (Experimental).
 */
@RequiredArgsConstructor
public class ToolAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List all tool IDs.
     * @return list of tool IDs
     */
    public List<String> listIds() {
        return http.get("/experimental/tool/ids", List.class);
    }

    /**
     * List tools with JSON schemas for a model.
     * @param provider provider ID (e.g., "anthropic") - REQUIRED
     * @param model model ID (e.g., "claude-3-5-sonnet") - REQUIRED
     * @return list of tools with schemas
     */
    public List<Map<String, Object>> list(String provider, String model) {
        Map<String, String> params = new HashMap<>();
        params.put("provider", provider);
        params.put("model", model);
        if (directory != null) params.put("directory", directory);
        return http.get("/experimental/tool", params, List.class);
    }
}