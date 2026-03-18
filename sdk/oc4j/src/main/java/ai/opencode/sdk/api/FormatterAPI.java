package ai.opencode.sdk.api;

import ai.opencode.sdk.http.HttpClient;
import lombok.RequiredArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * Formatter API for formatter status.
 */
@RequiredArgsConstructor
public class FormatterAPI {
    private final HttpClient http;
    private final String directory;

    /**
     * Get formatter status.
     * @return list of formatter statuses
     */
    public List<Object> status() {
        return http.getList("/formatter", null, Object.class);
    }
}