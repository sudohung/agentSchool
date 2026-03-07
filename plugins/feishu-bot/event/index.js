import { EventHandler, EventHandlerChain } from './handler.js';
import { SessionCreatedHandler } from './session-created.js';
import { SessionIdleHandler } from './session-idle.js';
import { ToolExecuteHandler } from './tool-execute.js';
import { SessionErrorHandler } from './session-error.js';
import { MessageUpdateHandler } from './message-update.js';
import { SessionStatusHandler } from './session-status.js';

export {
    EventHandler,
    EventHandlerChain,
    SessionCreatedHandler,
    SessionIdleHandler,
    ToolExecuteHandler,
    SessionErrorHandler,
    MessageUpdateHandler,
    SessionStatusHandler
};

/**
 * 创建事件处理器链
 */
export function createEventHandlerChain(project) {
    const chain = new EventHandlerChain();
    
    chain.add(new SessionCreatedHandler(project));
    chain.add(new MessageUpdateHandler());
    chain.add(new SessionIdleHandler());
    chain.add(new ToolExecuteHandler());
    chain.add(new SessionErrorHandler());
    chain.add(new SessionStatusHandler());

    return chain;
}
