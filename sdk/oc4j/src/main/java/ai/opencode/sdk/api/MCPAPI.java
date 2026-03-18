package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * MCP (Model Context Protocol) API for managing MCP servers.
 */
@RequiredArgsConstructor
public class MCPAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Get status of all MCP servers.
     * @return map of server name to status
     */
    public Map<String, Object> status() {
        return http.get("/mcp", Map.class);
    }

    /**
     * Add a new MCP server.
     * @param name server name
     * @param config server configuration
     * @return updated status map
     */
    public Map<String, Object> add(String name, Map<String, Object> config) {
        Map<String, Object> body = new HashMap<>();
        body.put("name", name);
        body.put("config", config);
        return http.post("/mcp", body, Map.class);
    }

    /**
     * Start OAuth authentication for MCP server.
     * @param name server name
     * @param method auth method index
     * @return authorization info
     */
    public Map<String, Object> authStart(String name, Integer method) {
        Map<String, Object> body = new HashMap<>();
        if (method != null) body.put("method", method);
        return http.post("/mcp/" + name + "/auth", body, Map.class);
    }

    /**
     * Start OAuth authentication for MCP server.
     * @param name server name
     * @return authorization info
     */
    public Map<String, Object> authStart(String name) {
        return authStart(name, null);
    }

    /**
     * Remove OAuth authentication for MCP server.
     * @param name server name
     * @return true if successful
     */
    public Boolean authRemove(String name) {
        return http.deleteWithResponse("/mcp/" + name + "/auth");
    }

    /**
     * Handle OAuth callback for MCP server.
     * @param name server name
     * @param code OAuth code
     * @param state OAuth state
     * @return true if successful
     */
    public Boolean authCallback(String name, String code, String state) {
        Map<String, String> body = new HashMap<>();
        body.put("code", code);
        if (state != null) body.put("state", state);
        return http.post("/mcp/" + name + "/auth/callback", body, Boolean.class);
    }

    /**
     * Connect to MCP server.
     * @param name server name
     * @param timeout connection timeout in ms
     * @return true if successful
     */
    public Boolean connect(String name, Integer timeout) {
        Map<String, Object> body = new HashMap<>();
        if (timeout != null) body.put("timeout", timeout);
        return http.post("/mcp/" + name + "/connect", body, Boolean.class);
    }

    /**
     * Connect to MCP server.
     * @param name server name
     * @return true if successful
     */
    public Boolean connect(String name) {
        return connect(name, null);
    }

    /**
     * Disconnect from MCP server.
     * @param name server name
     * @return true if successful
     */
    public Boolean disconnect(String name) {
        return http.post("/mcp/" + name + "/disconnect", null, Boolean.class);
    }

    /**
     * Authenticate MCP OAuth - start OAuth flow and wait for callback.
     * Opens browser for user authentication.
     * @param name server name
     * @return MCP status after authentication
     */
    public Map<String, Object> authAuthenticate(String name) {
        return http.post("/mcp/" + name + "/auth/authenticate", null, Map.class);
    }
}