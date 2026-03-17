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
        return http.get("/file", List.class);
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
        return http.get("/file/content", Map.class);
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
        return http.get("/find", List.class);
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
        return http.get("/find/file", List.class);
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
        return http.get("/find/symbol", List.class);
    }
}