package ai.openclaw.ocjbot.event;

public interface EventHandler<T> {
    
    void handle(Event<T> event);
}