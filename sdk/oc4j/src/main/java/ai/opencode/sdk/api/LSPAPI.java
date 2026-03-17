package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * LSP (Language Server Protocol) API.
 */
@RequiredArgsConstructor
public class LSPAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Get LSP server status.
     * @return list of LSP server statuses
     */
    public List<Map<String, Object>> status() {
        return http.get("/lsp", List.class);
    }
}