package ai.opencode.sdk.http;

import java.io.Closeable;
import java.util.Iterator;

public interface SseListener<T> extends Closeable {
    void onEvent(T event);
    void onError(Throwable error);
    void onComplete();
    
    interface Factory {
        <T> SseListener<T> create(Iterator<T> iterator);
    }
}