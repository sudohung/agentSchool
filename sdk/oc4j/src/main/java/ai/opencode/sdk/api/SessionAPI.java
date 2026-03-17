package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import ai.opencode.sdk.model.session.Session;
import ai.opencode.sdk.model.session.Todo;
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
     * @param directory directory
     * @return created session
     */
    public Session create(String title, String directory) {
        Map<String, String> body = new HashMap<>();
        if (title != null) body.put("title", title);
        if (directory != null) body.put("directory", directory);
        return http.post("/session", body, Session.class);
    }

    /**
     * Delete a session.
     * @param sessionId session ID
     */
    public void delete(String sessionId) {
        http.delete("/session/" + sessionId);
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
     * Get session status.
     * @param sessionId session ID
     * @return status
     */
    public String status(String sessionId) {
        return http.get("/session/" + sessionId + "/status", String.class);
    }
}
