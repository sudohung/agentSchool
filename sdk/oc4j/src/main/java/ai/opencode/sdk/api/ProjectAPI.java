package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
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
     * List all projects.
     * @return list of projects
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

    /**
     * Update project properties.
     * @param projectId project ID
     * @param name new project name
     * @param icon icon configuration
     * @param commands commands configuration
     * @return updated project
     */
    public Map<String, Object> update(String projectId, String name, 
                                      Map<String, Object> icon, Map<String, Object> commands) {
        Map<String, Object> body = new HashMap<>();
        if (name != null) body.put("name", name);
        if (icon != null) body.put("icon", icon);
        if (commands != null) body.put("commands", commands);
        return http.patch("/project/" + projectId, body, Map.class);
    }

    /**
     * Update project name.
     * @param projectId project ID
     * @param name new project name
     * @return updated project
     */
    public Map<String, Object> update(String projectId, String name) {
        return update(projectId, name, null, null);
    }

    /**
     * Initialize git repository for the current project.
     * @return project after git initialization
     */
    public Map<String, Object> initGit() {
        return http.post("/project/git/init", null, Map.class);
    }
}