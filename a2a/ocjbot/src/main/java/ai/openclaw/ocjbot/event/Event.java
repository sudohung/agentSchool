package ai.openclaw.ocjbot.event;

import java.time.Instant;

public record Event<T>(
    Class<T> type,
    T data,
    String source,
    Instant timestamp
) {
    public static <T> Event<T> of(Class<T> type, T data) {
        return new Event<>(type, data, null, Instant.now());
    }
    
    public static <T> Event<T> of(Class<T> type, T data, String source) {
        return new Event<>(type, data, source, Instant.now());
    }
}