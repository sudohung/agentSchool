package ai.openclaw.ocjbot.runtime.model;

import java.util.function.Consumer;

/**
 * 事件订阅句柄
 */
public interface EventSubscription extends AutoCloseable {
    
    /**
     * 获取订阅 ID
     */
    String getSubscriptionId();
    
    /**
     * 是否活跃
     */
    boolean isActive();
    
    /**
     * 取消订阅
     */
    void unsubscribe();
    
    @Override
    default void close() {
        unsubscribe();
    }
}