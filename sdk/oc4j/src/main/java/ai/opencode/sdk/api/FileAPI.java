package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * File API for file operations.
 */
@RequiredArgsConstructor
public class FileAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List files and directories.
     * @param path directory path (default: ".")
     * @return list of file nodes
     */
    public List<Map<String, Object>> list(String path) {
        Map<String, String> params = new HashMap<>();
        params.put("path", path);
        if (directory != null) params.put("directory", directory);
        return http.get("/file", params, List.class);
    }

    /**
     * List files in current directory.
     * @return list of file nodes
     */
    public List<Map<String, Object>> list() {
        return list(".");
    }

    /**
     * Read file content.
     * @param path file path
     * @return file content
     */
    public Map<String, Object> read(String path) {
        Map<String, String> params = new HashMap<>();
        params.put("path", path);
        if (directory != null) params.put("directory", directory);
        return http.get("/file/content", params, Map.class);
    }

    /**
     * Get Git file status.
     * @return list of file statuses
     */
    public List<Map<String, Object>> status() {
        return http.get("/file/status", List.class);
    }

    /**
     * Search for text in files.
     * @param pattern regex pattern
     * @param path optional path scope
     * @return list of search matches
     */
    public List<Map<String, Object>> searchText(String pattern, String path) {
        Map<String, String> params = new HashMap<>();
        params.put("pattern", pattern);
        if (path != null) params.put("path", path);
        if (directory != null) params.put("directory", directory);
        return http.get("/find", params, List.class);
    }

    /**
     * Search for text in files.
     * @param pattern regex pattern
     * @return list of search matches
     */
    public List<Map<String, Object>> searchText(String pattern) {
        return searchText(pattern, null);
    }

    /**
     * Find files by name.
     * @param query search query (fuzzy match)
     * @param type filter by "file" or "directory"
     * @param limit max results (1-200)
     * @return list of file paths
     */
    public List<String> findFiles(String query, String type, Integer limit) {
        Map<String, Object> params = new HashMap<>();
        params.put("query", query);
        if (type != null) params.put("type", type);
        if (limit != null) params.put("limit", limit);
        if (directory != null) params.put("directory", directory);
        return http.get("/find/file", params, List.class);
    }

    /**
     * Find files by name.
     * @param query search query
     * @return list of file paths
     */
    public List<String> findFiles(String query) {
        return findFiles(query, null, null);
    }

    /**
     * Find workspace symbols.
     * @param query symbol name query
     * @return list of symbols
     */
    public List<Map<String, Object>> findSymbols(String query) {
        Map<String, String> params = new HashMap<>();
        params.put("query", query);
        if (directory != null) params.put("directory", directory);
        return http.get("/find/symbol", params, List.class);
    }
}