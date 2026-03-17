package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * File API for managing files.
 */
@RequiredArgsConstructor
public class FileAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List files.
     * @param path file path
     * @return list of files
     */
    public List<Map<String, Object>> list(String path) {
        return http.get("/file", List.class);
    }

    /**
     * Read file content.
     * @param path file path
     * @return file content
     */
    public Map<String, Object> read(String path) {
        return http.get("/file/content", Map.class);
    }

    /**
     * Get file status.
     * @return list of file status
     */
    public List<Map<String, Object>> status() {
        return http.get("/file/status", List.class);
    }
}
