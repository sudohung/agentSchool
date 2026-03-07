import { EventHandler } from './handler.js';
import { sendEventNotification } from '../webhook/index.js';

export class SessionIdleHandler extends EventHandler {
    constructor() {
        super('session.idle');
    }

    async process(event, context) {
//        return await sendEventNotification(
//            "会话已完成",
//            `会话 ${event.properties?.sessionID} 已完成处理`
//        );
    }
}
