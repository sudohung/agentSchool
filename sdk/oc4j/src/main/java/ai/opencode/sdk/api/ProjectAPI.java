package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.project.Project;
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
    public List<Project> list() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.getList("/project", params, Project.class);
    }

    /**
     * Get current project.
     * @return current project
     */
    public Project current() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.get("/project/current", params, Project.class);
    }

    /**
     * Update project properties.
     * @param projectId project ID
     * @param name new project name
     * @param icon icon configuration
     * @param commands commands configuration
     * @return updated project
     */
    public Project update(String projectId, String name, 
                          Map<String, Object> icon, Map<String, Object> commands) {
        Map<String, Object> body = new HashMap<>();
        if (name != null) body.put("name", name);
        if (icon != null) body.put("icon", icon);
        if (commands != null) body.put("commands", commands);
        return http.patch("/project/" + projectId, body, Project.class);
    }

    /**
     * Update project name.
     * @param projectId project ID
     * @param name new project name
     * @return updated project
     */
    public Project update(String projectId, String name) {
        return update(projectId, name, null, null);
    }

    /**
     * Initialize git repository for the current project.
     * @return project after git initialization
     */
    public Project initGit() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.post("/project/git/init", null, Project.class);
    }
}