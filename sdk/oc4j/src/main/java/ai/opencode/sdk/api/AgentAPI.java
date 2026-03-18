package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.agent.Agent;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
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
     * @return list of agents
     */
    public List<Agent> list() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.getList("/agent", params, Agent.class);
    }
}
