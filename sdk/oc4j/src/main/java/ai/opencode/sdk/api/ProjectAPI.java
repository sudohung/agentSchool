package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Project API for managing projects.
 */
@RequiredArgsConstructor
public class ProjectAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List projects.
     * @return projects
     */
    public List<Map<String, Object>> list() {
        return http.get("/project", List.class);
    }

    /**
     * Get current project.
     * @return current project
     */
    public Map<String, Object> current() {
        return http.get("/project/current", Map.class);
    }
}
