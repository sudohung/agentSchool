package ai.openclaw.ocjbot.runtime.opencode;

import ai.openclaw.ocjbot.runtime.model.EventSubscription;
import ai.openclaw.ocjbot.runtime.model.RuntimeEvent;
import ai.openclaw.ocjbot.runtime.model.RuntimeGlobalEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Iterator;
import java.util.Map;
import java.util.function.Consumer;
import java.util.function.Function;

/**
 * 事件订阅实现
 */
class EventSubscriptionImpl implements EventSubscription {
    
    private static final Logger log = LoggerFactory.getLogger(EventSubscriptionImpl.class);
    
    private final String subscriptionId;
    private final IteratorSupplier iteratorSupplier;
    private final Consumer<Object> eventHandler;
    private final Function<Object, Object> converter;
    private volatile boolean active = true;
    private volatile Thread thread;
    
    @SuppressWarnings("unchecked")
    <T, R> EventSubscriptionImpl(
            String subscriptionId, 
            IteratorSupplier iteratorSupplier,
            Consumer<R> eventHandler,
            Function<T, R> converter) {
        this.subscriptionId = subscriptionId;
        this.iteratorSupplier = iteratorSupplier;
        this.eventHandler = (Consumer<Object>) eventHandler;
        this.converter = (Function<Object, Object>) converter;
    }
    
    @Override
    public String getSubscriptionId() {
        return subscriptionId;
    }
    
    @Override
    public boolean isActive() {
        return active && thread != null && thread.isAlive();
    }
    
    @Override
    public void unsubscribe() {
        active = false;
        if (thread != null) {
            thread.interrupt();
        }
    }
    
    @SuppressWarnings("unchecked")
    void run() {
        thread = Thread.currentThread();
        try {
            Iterator<T> iterator = (Iterator<T>) iteratorSupplier.get();
            while (active && iterator.hasNext()) {
                T event = iterator.next();
                if (event != null) {
                    R converted = ((Function<T, R>) converter).apply(event);
                    eventHandler.accept(converted);
                }
            }
        } catch (Exception e) {
            if (active) {
                log.debug("Event subscription interrupted: {}", e.getMessage());
            }
        }
    }
    
    @FunctionalInterface
    interface IteratorSupplier {
        Iterator<?> get();
    }
}