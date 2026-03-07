/**
 * 事件处理器基类
 */
export class EventHandler {
    constructor(eventType) {
        this.eventType = eventType;
        this.nextHandler = null;
    }

    setNext(handler) {
        this.nextHandler = handler;
        return handler;
    }

    async handle(event, context) {
        if (event.type === this.eventType) {
            return await this.process(event, context);
        }
        if (this.nextHandler) {
            return await this.nextHandler.handle(event, context);
        }
        return null;
    }

    async process(event, context) {
        throw new Error('process method must be implemented');
    }
}

/**
 * 事件处理器链
 */
export class EventHandlerChain {
    constructor() {
        this.handlers = [];
    }

    add(handler) {
        this.handlers.push(handler);
        return this;
    }

    async handle(event, context) {
        // 排除 server.heartbeat
        if (event.type === 'server.heartbeat') {
            return null;
        }
        console.log(`[AgentEventHandlerChain] 收到事件：${event.type}, event: ${JSON.stringify(event)}`);

        for (const handler of this.handlers) {
            if (event.type === handler.eventType) {
//                console.log(`[EventHandlerChain] 处理事件：${handler.eventType}, event: ${JSON.stringify(event)}`);
                return await handler.process(event, context);
            }
        }
        return null;
    }
}
