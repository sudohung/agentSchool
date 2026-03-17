package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Agent API for managing agents.
 */
@RequiredArgsConstructor
public class AgentAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List agents.
     * @return agents
     */
    public List<Map<String, Object>> list() {
        return http.get("/agent", List.class);
    }
}
