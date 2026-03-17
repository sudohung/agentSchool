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
     * @param provider provider ID (e.g., "anthropic")
     * @param model model ID (e.g., "claude-3-5-sonnet")
     * @return list of tools with schemas
     */
    public List<Map<String, Object>> list(String provider, String model) {
        return http.get("/experimental/tool", List.class);
    }
}