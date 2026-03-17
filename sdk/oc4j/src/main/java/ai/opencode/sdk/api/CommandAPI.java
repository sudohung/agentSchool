package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Command API for managing commands.
 */
@RequiredArgsConstructor
public class CommandAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * List commands.
     * @return commands
     */
    public List<Map<String, Object>> list() {
        return http.get("/command", List.class);
    }
}
