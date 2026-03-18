package ai.opencode.sdk.http;

import java.util.Iterator;
import java.util.NoSuchElementException;
import java.util.function.Consumer;

public class SseIterator<T> implements Iterator<T>, AutoCloseable {
    private final java.io.BufferedReader reader;
    private final java.util.function.Function<String, T> parser;
    private T nextEvent;
    private boolean closed = false;

    public SseIterator(java.io.InputStream inputStream, java.util.function.Function<String, T> parser) {
        this.reader = new java.io.BufferedReader(new java.io.InputStreamReader(inputStream, java.nio.charset.StandardCharsets.UTF_8));
        this.parser = parser;
    }

    @Override
    public boolean hasNext() {
        if (closed) {
            return false;
        }
        if (nextEvent != null) {
            return true;
        }
        try {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("data: ")) {
                    String data = line.substring(6);
                    if (!data.isEmpty()) {
                        nextEvent = parser.apply(data);
                        if (nextEvent != null) {
                            return true;
                        }
                    }
                }
            }
            close();
            return false;
        } catch (Exception e) {
            close();
            throw new RuntimeException("Failed to read SSE stream", e);
        }
    }

    @Override
    public T next() {
        if (!hasNext()) {
            throw new NoSuchElementException();
        }
        T event = nextEvent;
        nextEvent = null;
        return event;
    }

    @Override
    public void close() {
        if (!closed) {
            closed = true;
            try {
                reader.close();
            } catch (Exception ignored) {
            }
        }
    }
}