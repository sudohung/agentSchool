package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.session.Session;
import ai.opencode.sdk.model.session.Todo;
import ai.opencode.sdk.model.common.FileDiff;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Session API for managing sessions.
 */
@RequiredArgsConstructor
public class SessionAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List all sessions.
     * @return list of sessions
     */
    public List<Session> list() {
        return http.get("/session", List.class);
    }

    /**
     * List sessions with filters.
     * @param workspace workspace ID
     * @param roots only root sessions
     * @param start start offset
     * @param search search term
     * @param limit max results
     * @return list of sessions
     */
    public List<Session> list(String workspace, Boolean roots, Integer start, String search, Integer limit) {
        Map<String, Object> params = new HashMap<>();
        if (workspace != null) params.put("workspace", workspace);
        if (roots != null) params.put("roots", roots);
        if (start != null) params.put("start", start);
        if (search != null) params.put("search", search);
        if (limit != null) params.put("limit", limit);
        return http.get("/session", params, List.class);
    }

    /**
     * Get session by ID.
     * @param sessionId session ID
     * @return session
     */
    public Session get(String sessionId) {
        return http.get("/session/" + sessionId, Session.class);
    }

    /**
     * Create a new session.
     * @param title session title
     * @return created session
     */
    public Session create(String title) {
        return create(title, null, null);
    }

    /**
     * Create a new session.
     * @param title session title
     * @param parentId parent session ID
     * @param permission permission rules
     * @return created session
     */
    public Session create(String title, String parentId, List<Map<String, Object>> permission) {
        Map<String, Object> body = new HashMap<>();
        if (title != null) body.put("title", title);
        if (parentId != null) body.put("parentID", parentId);
        if (permission != null) body.put("permission", permission);
        return http.post("/session", body, Session.class);
    }

    /**
     * Delete a session.
     * @param sessionId session ID
     * @return true if deleted
     */
    public Boolean delete(String sessionId) {
        return http.deleteWithResponse("/session/" + sessionId);
    }

    /**
     * Update session title.
     * @param sessionId session ID
     * @param title new title
     * @return updated session
     */
    public Session update(String sessionId, String title) {
        Map<String, String> body = new HashMap<>();
        body.put("title", title);
        return http.patch("/session/" + sessionId, body, Session.class);
    }

    /**
     * Get session status for all sessions.
     * @return map of session ID to status
     */
    public Map<String, Object> status() {
        return http.get("/session/status", Map.class);
    }

    /**
     * Get child sessions.
     * @param sessionId session ID
     * @return list of child sessions
     */
    public List<Session> children(String sessionId) {
        return http.get("/session/" + sessionId + "/children", List.class);
    }

    /**
     * Get session todos.
     * @param sessionId session ID
     * @return list of todos
     */
    public List<Todo> todos(String sessionId) {
        return http.get("/session/" + sessionId + "/todo", List.class);
    }

    /**
     * Abort a running session.
     * @param sessionId session ID
     * @return true if aborted
     */
    public Boolean abort(String sessionId) {
        return http.post("/session/" + sessionId + "/abort", null, Boolean.class);
    }

    /**
     * Share a session.
     * @param sessionId session ID
     * @return updated session
     */
    public Session share(String sessionId) {
        return http.post("/session/" + sessionId + "/share", null, Session.class);
    }

    /**
     * Unshare a session.
     * @param sessionId session ID
     * @return updated session
     */
    public Session unshare(String sessionId) {
        return http.deleteWithResponse("/session/" + sessionId + "/share") ? 
            get(sessionId) : null;
    }

    /**
     * Fork a session at a message.
     * @param sessionId session ID
     * @param messageId message ID to fork at
     * @return new forked session
     */
    public Session fork(String sessionId, String messageId) {
        Map<String, String> body = new HashMap<>();
        if (messageId != null) body.put("messageID", messageId);
        return http.post("/session/" + sessionId + "/fork", body, Session.class);
    }

    /**
     * Fork a session.
     * @param sessionId session ID
     * @return new forked session
     */
    public Session fork(String sessionId) {
        return fork(sessionId, null);
    }

    /**
     * Get diff for a session.
     * @param sessionId session ID
     * @param messageId message ID (optional)
     * @return list of file diffs
     */
    public List<FileDiff> diff(String sessionId, String messageId) {
        return http.get("/session/" + sessionId + "/diff", List.class);
    }

    /**
     * Get diff for a session.
     * @param sessionId session ID
     * @return list of file diffs
     */
    public List<FileDiff> diff(String sessionId) {
        return diff(sessionId, null);
    }

    /**
     * Summarize a session.
     * @param sessionId session ID
     * @param providerId provider ID
     * @param modelId model ID
     * @return true if successful
     */
    public Boolean summarize(String sessionId, String providerId, String modelId) {
        Map<String, String> body = new HashMap<>();
        body.put("providerID", providerId);
        body.put("modelID", modelId);
        return http.post("/session/" + sessionId + "/summarize", body, Boolean.class);
    }

    /**
     * Revert a message.
     * @param sessionId session ID
     * @param messageId message ID
     * @param partId part ID (optional)
     * @return true if successful
     */
    public Boolean revert(String sessionId, String messageId, String partId) {
        Map<String, String> body = new HashMap<>();
        body.put("messageID", messageId);
        if (partId != null) body.put("partID", partId);
        return http.post("/session/" + sessionId + "/revert", body, Boolean.class);
    }

    /**
     * Revert a message.
     * @param sessionId session ID
     * @param messageId message ID
     * @return true if successful
     */
    public Boolean revert(String sessionId, String messageId) {
        return revert(sessionId, messageId, null);
    }

    /**
     * Unrevert reverted messages.
     * @param sessionId session ID
     * @return true if successful
     */
    public Boolean unrevert(String sessionId) {
        return http.post("/session/" + sessionId + "/unrevert", null, Boolean.class);
    }

    /**
     * Initialize session (create AGENTS.md).
     * @param sessionId session ID
     * @param messageId message ID
     * @param providerId provider ID
     * @param modelId model ID
     * @return true if successful
     */
    public Boolean init(String sessionId, String messageId, String providerId, String modelId) {
        Map<String, String> body = new HashMap<>();
        body.put("messageID", messageId);
        body.put("providerID", providerId);
        body.put("modelID", modelId);
        return http.post("/session/" + sessionId + "/init", body, Boolean.class);
    }
}