package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.file.FileNode;
import ai.opencode.sdk.model.file.FileContent;
import ai.opencode.sdk.model.file.FileStatus;
import ai.opencode.sdk.model.file.TextSearchMatch;
import ai.opencode.sdk.model.file.Symbol;
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
    public List<FileNode> list(String path) {
        Map<String, String> params = new HashMap<>();
        params.put("path", path);
        if (directory != null) params.put("directory", directory);
        return http.getList("/file", params, FileNode.class);
    }

    /**
     * List files in current directory.
     * @return list of file nodes
     */
    public List<FileNode> list() {
        return list(".");
    }

    /**
     * Read file content.
     * @param path file path
     * @return file content
     */
    public FileContent read(String path) {
        Map<String, String> params = new HashMap<>();
        params.put("path", path);
        if (directory != null) params.put("directory", directory);
        return http.get("/file/content", params, FileContent.class);
    }

    /**
     * Get Git file status.
     * @return list of file statuses
     */
    public List<FileStatus> status() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) params.put("directory", directory);
        return http.getList("/file/status", params, FileStatus.class);
    }

    /**
     * Search for text in files.
     * @param pattern regex pattern
     * @param path optional path scope
     * @return list of search matches
     */
    public List<TextSearchMatch> searchText(String pattern, String path) {
        Map<String, String> params = new HashMap<>();
        params.put("pattern", pattern);
        if (path != null) params.put("path", path);
        if (directory != null) params.put("directory", directory);
        return http.getList("/find", params, TextSearchMatch.class);
    }

    /**
     * Search for text in files.
     * @param pattern regex pattern
     * @return list of search matches
     */
    public List<TextSearchMatch> searchText(String pattern) {
        return searchText(pattern, null);
    }

    /**
     * Find files by name.
     * @param query search query (fuzzy match)
     * @param type filter by "file" or "directory"
     * @param limit max results (1-200)
     * @param dirs comma-separated list of directories to search
     * @return list of file paths
     */
    public List<String> findFiles(String query, String type, Integer limit, String dirs) {
        Map<String, Object> params = new HashMap<>();
        params.put("query", query);
        if (type != null) params.put("type", type);
        if (limit != null) params.put("limit", limit);
        if (dirs != null) params.put("dirs", dirs);
        if (directory != null) params.put("directory", directory);
        return http.get("/find/file", params, List.class);
    }

    /**
     * Find files by name.
     * @param query search query (fuzzy match)
     * @param type filter by "file" or "directory"
     * @param limit max results (1-200)
     * @return list of file paths
     */
    public List<String> findFiles(String query, String type, Integer limit) {
        return findFiles(query, type, limit, null);
    }

    /**
     * Find files by name.
     * @param query search query
     * @return list of file paths
     */
    public List<String> findFiles(String query) {
        return findFiles(query, null, null, null);
    }

    /**
     * Find workspace symbols.
     * @param query symbol name query
     * @return list of symbols
     */
    public List<Symbol> findSymbols(String query) {
        Map<String, String> params = new HashMap<>();
        params.put("query", query);
        if (directory != null) params.put("directory", directory);
        return http.getList("/find/symbol", params, Symbol.class);
    }
}