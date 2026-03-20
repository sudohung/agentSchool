package ai.openclaw.ocjbot.event;

public interface EventBus {
    
    <T> void publish(Event<T> event);
    
    <T> void subscribe(Class<T> eventType, EventHandler<T> handler);
    
    <T> void unsubscribe(Class<T> eventType, EventHandler<T> handler);
}