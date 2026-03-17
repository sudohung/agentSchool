package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.Map;

/**
 * Global API for global operations.
 */
@RequiredArgsConstructor
public class GlobalAPI {
    private final HttpClient http;

    /**
     * Get health status.
     * @return health info
     */
    public Map<String, Object> health() {
        return http.get("/global/health", Map.class);
    }

    /**
     * Get global configuration.
     * @return global config
     */
    public Map<String, Object> config() {
        return http.get("/global/config", Map.class);
    }

    /**
     * Update global configuration.
     * @param config new configuration
     * @return updated config
     */
    public Map<String, Object> updateConfig(Map<String, Object> config) {
        return http.patch("/global/config", config, Map.class);
    }

    /**
     * Dispose instance.
     * @return true if successful
     */
    public Boolean dispose() {
        return http.post("/global/dispose", null, Boolean.class);
    }

    /**
     * Write a log entry.
     * @param entry log entry with service, level, message, and optional extra data
     * @return true if log was written successfully
     */
    public Boolean log(Map<String, Object> entry) {
        return http.post("/log", entry, Boolean.class);
    }

    /**
     * Write a simple log message.
     * @param level log level (debug, info, warn, error)
     * @param message log message
     * @param service service name (default: "opencode-sdk")
     * @param extra optional additional data
     * @return true if log was written successfully
     */
    public Boolean logMessage(String level, String message, String service, Map<String, Object> extra) {
        Map<String, Object> entry = new HashMap<>();
        entry.put("service", service != null ? service : "opencode-sdk");
        entry.put("level", level);
        entry.put("message", message);
        if (extra != null) {
            entry.put("extra", extra);
        }
        return log(entry);
    }

    /**
     * Write a simple log message with default service name.
     * @param level log level (debug, info, warn, error)
     * @param message log message
     * @return true if log was written successfully
     */
    public Boolean logMessage(String level, String message) {
        return logMessage(level, message, "opencode-sdk", null);
    }
}
