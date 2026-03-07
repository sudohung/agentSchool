import { EventHandler } from './handler.js';
import { sendEventNotification } from '../webhook/index.js';

export class MessageUpdateHandler extends EventHandler {
    constructor() {
        super('message.updated');
    }

    async process(event, context) {
        return
//        return await sendEventNotification(
//            `OpenCode sessionID: ${event.properties?.info?.sessionID} 消息更新`,
//            `message ID: ${event.properties?.info?.id}`
//        );
    }
}
