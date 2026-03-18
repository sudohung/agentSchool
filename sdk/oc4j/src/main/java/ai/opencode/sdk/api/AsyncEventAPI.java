package ai.opencode.sdk.api;

import ai.opencode.sdk.http.AsyncHttpClient;
import ai.opencode.sdk.model.event.Event;
import ai.opencode.sdk.model.event.GlobalEvent;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Flow;

/**
 * Async Event API client for SSE streaming.
 * Equivalent to Python SDK's AsyncEventAPI class.
 */
public class AsyncEventAPI {
    private final AsyncHttpClient http;
    private final ObjectMapper mapper;
    private final String directory;
    private final String workspace;

    public AsyncEventAPI(AsyncHttpClient http, String directory, String workspace) {
        this.http = http;
        this.mapper = new ObjectMapper();
        this.directory = directory;
        this.workspace = workspace;
    }

    /**
     * Subscribe to global events (SSE stream).
     * Equivalent to Python: async subscribe_global()
     * Endpoint: GET /global/event
     */
    public Flow.Publisher<GlobalEvent> subscribeGlobal() {
        return http.streamSse("/global/event", this::parseGlobalEvent);
    }

    /**
     * Subscribe to project events (SSE stream).
     * Equivalent to Python: async subscribe()
     * Endpoint: GET /event
     */
    public Flow.Publisher<Event> subscribe() {
        Map<String, String> params = getParams();
        return http.streamSse("/event", params, this::parseEvent);
    }

    /**
     * Subscribe to project events with custom directory (SSE stream).
     * Endpoint: GET /event?directory=...
     */
    public Flow.Publisher<Event> subscribe(String directory) {
        Map<String, String> params = new HashMap<>();
        if (directory != null) {
            params.put("directory", directory);
        }
        if (workspace != null) {
            params.put("workspace", workspace);
        }
        return http.streamSse("/event", params, this::parseEvent);
    }

    private Map<String, String> getParams() {
        Map<String, String> params = new HashMap<>();
        if (directory != null) {
            params.put("directory", directory);
        }
        if (workspace != null) {
            params.put("workspace", workspace);
        }
        return params;
    }

    private GlobalEvent parseGlobalEvent(String data) {
        try {
            return mapper.readValue(data, GlobalEvent.class);
        } catch (Exception e) {
            return null;
        }
    }

    private Event parseEvent(String data) {
        try {
            return mapper.readValue(data, Event.class);
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
}