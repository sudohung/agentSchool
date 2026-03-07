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
        for (const handler of this.handlers) {
            if (event.type === handler.eventType) {
                return await handler.process(event, context);
            }
        }
        return null;
    }
}
