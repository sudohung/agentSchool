package ai.openclaw.ocjbot.runtime.opencode;

import ai.openclaw.ocjbot.runtime.model.EventSubscription;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Iterator;
import java.util.function.Consumer;
import java.util.function.Function;

class EventSubscriptionImpl implements EventSubscription {
    
    private static final Logger log = LoggerFactory.getLogger(EventSubscriptionImpl.class);
    
    private final String subscriptionId;
    private volatile boolean active = true;
    private volatile Thread thread;
    
    EventSubscriptionImpl(String subscriptionId) {
        this.subscriptionId = subscriptionId;
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
}